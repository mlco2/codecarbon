import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";
import { EmissionsTimeSeries } from "@/api/schemas";
import * as React from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { ExportCsvButton } from "@/components/export-csv-button";
import ChartRow from "@/components/chart-row";
import ChartSection from "@/components/chart-section";
import ChartSkeleton from "@/components/chart-skeleton";
import { getEmissionsTimeSeries } from "@/api/runs";
import { exportEmissionsTimeSeriesCsv } from "@/utils/export";
import { pickTimeFormat } from "@/helpers/time-axis";
import { format } from "date-fns";
import { Cpu, HardDrive, Server } from "lucide-react";

interface EmissionsTimeSeriesChartProps {
    isPublicView: boolean;
    runId: string;
    projectName?: string;
    experimentName?: string;
}

const chartConfig = {
    emissions_rate: {
        label: "Emissions Rate",
        color: "hsl(var(--primary))",
    },
    energy_consumed: {
        label: "Energy Consumed",
        color: "hsl(var(--secondary))",
    },
} satisfies ChartConfig;

type TimeSeriesTooltipPayload = Array<{
    payload: {
        ts: number;
    };
}>;

export default function EmissionsTimeSeriesChart({
    isPublicView,
    runId,
    projectName = "project",
    experimentName,
}: EmissionsTimeSeriesChartProps) {
    const [activeChart, setActiveChart] =
        React.useState<keyof typeof chartConfig>("emissions_rate");
    const [emissionTimeSeries, setEmissionTimeSeries] =
        React.useState<EmissionsTimeSeries | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);

    React.useEffect(() => {
        if (!runId) return;
        let cancelled = false;
        (async () => {
            setIsLoading(true);
            try {
                const data = await getEmissionsTimeSeries(runId);
                if (!cancelled) setEmissionTimeSeries(data);
            } catch (error) {
                console.error("Failed to fetch emissions time series:", error);
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [runId]);

    if (!runId) {
        return null;
    }

    if (isLoading) {
        return <ChartSkeleton height={300} />;
    }

    if (!emissionTimeSeries || !emissionTimeSeries.metadata) {
        return <div>No data available</div>;
    }

    // Recharts category axis distributes ticks evenly by index, so 200 samples
    // taken in the same minute produce 200 identical-looking labels. Re-key on
    // a numeric timestamp and a time scale so the axis spaces ticks by *when*
    // points happened, not by how many of them there are.
    const points = emissionTimeSeries.emissions.map((e) => ({
        ...e,
        ts: new Date(e.timestamp).getTime(),
    }));
    const spanMs = points.length
        ? points[points.length - 1].ts - points[0].ts
        : 0;
    const tickFmt = pickTimeFormat(spanMs);

    return (
        <ChartRow insetTop>
            <ChartSection
                title="Emissions time series"
                description="Showing emissions rate and energy consumed over time"
                action={
                    !isPublicView && (
                        <ExportCsvButton
                            isDisabled={
                                !emissionTimeSeries ||
                                !emissionTimeSeries.emissions.length
                            }
                            onDownload={async () => {
                                if (!emissionTimeSeries) return;
                                exportEmissionsTimeSeriesCsv(
                                    emissionTimeSeries,
                                    projectName,
                                    experimentName,
                                );
                            }}
                            loadingMessage="Exporting time series..."
                            successMessage="Time series exported successfully"
                            errorMessage="Failed to export time series"
                        />
                    )
                }
            >
                <div className="flex flex-wrap gap-2">
                    {Object.keys(chartConfig).map((key) => {
                        const chart = key as keyof typeof chartConfig;
                        return (
                            <button
                                key={chart}
                                type="button"
                                data-active={activeChart === chart}
                                className="type-mono-medium type-row-meta cursor-pointer rounded-field px-4 py-2 text-cc-gray outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime data-[active=true]:bg-cc-darkest-gray data-[active=true]:text-cc-lime motion-reduce:transition-none"
                                onClick={() => setActiveChart(chart)}
                            >
                                {chartConfig[chart].label}
                            </button>
                        );
                    })}
                </div>
                <ChartContainer
                    config={chartConfig}
                    className="aspect-auto h-[250px] w-full"
                >
                    <LineChart
                        data={points}
                        margin={{
                            left: 12,
                            right: 12,
                        }}
                    >
                        <CartesianGrid vertical={false} />
                        <XAxis
                            dataKey="ts"
                            type="number"
                            scale="time"
                            domain={["dataMin", "dataMax"]}
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            minTickGap={48}
                            tickFormatter={(value) =>
                                format(new Date(value), tickFmt)
                            }
                        />
                        <YAxis
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                        />
                        <ChartTooltip
                            content={
                                <ChartTooltipContent
                                    className="w-[180px]"
                                    labelFormatter={(_, payload) => {
                                        const tooltipPayload = payload as
                                            | TimeSeriesTooltipPayload
                                            | undefined;
                                        const point =
                                            tooltipPayload?.[0]?.payload;

                                        if (!point) {
                                            return "";
                                        }

                                        return format(
                                            new Date(point.ts),
                                            "MMM d, yyyy HH:mm:ss",
                                        );
                                    }}
                                />
                            }
                        />
                        <Line
                            dataKey={activeChart}
                            type="monotone"
                            stroke={chartConfig[activeChart].color}
                            strokeWidth={2}
                            dot={false}
                        />
                    </LineChart>
                </ChartContainer>
            </ChartSection>
            <ChartSection
                title="Run metadata"
                description="Hardware and environment details"
            >
                <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                        <Cpu className="h-5 w-5" />
                        <span className="font-medium">CPU:</span>
                        <span>
                            {emissionTimeSeries.metadata.cpu_model} (
                            {emissionTimeSeries.metadata.cpu_count} cores)
                        </span>
                    </div>
                    {emissionTimeSeries.metadata.gpu_model && (
                        <div className="flex items-center space-x-2">
                            <Server className="h-5 w-5" />
                            <span className="font-medium">GPU:</span>
                            <span>
                                {emissionTimeSeries.metadata.gpu_model} (
                                {emissionTimeSeries.metadata.gpu_count})
                            </span>
                        </div>
                    )}
                    <div className="flex items-center space-x-2">
                        <HardDrive className="h-5 w-5" />
                        <span className="font-medium">RAM:</span>
                        <span>
                            {emissionTimeSeries.metadata.ram_total_size} GB
                        </span>
                    </div>
                    <div>
                        <span className="font-medium">OS:</span>{" "}
                        {emissionTimeSeries.metadata.os}
                    </div>
                    <div>
                        <span className="font-medium">Python:</span>{" "}
                        {emissionTimeSeries.metadata.python_version}
                    </div>
                    <div>
                        <span className="font-medium">Region:</span>{" "}
                        {emissionTimeSeries.metadata.region}
                    </div>
                </div>
            </ChartSection>
        </ChartRow>
    );
}
