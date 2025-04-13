"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";
import * as React from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { ExportCsvButton } from "@/components/export-csv-button";
import { getEmissionsTimeSeries } from "@/server-functions/runs";
import { exportEmissionsTimeSeriesCsv } from "@/utils/export";
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
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        async function fetchData() {
            setIsLoading(true);
            try {
                const data = await getEmissionsTimeSeries(runId);
                setEmissionTimeSeries(data);
            } catch (error) {
                console.error("Failed to fetch emissions time series:", error);
            } finally {
                setIsLoading(false);
            }
        }

        if (runId) {
            fetchData();
        }
    }, [runId]);

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (!emissionTimeSeries || !emissionTimeSeries.metadata) {
        return <div>No data available</div>;
    }

    return (
        <div className="grid gap-4 md:grid-cols-2">
            <Card>
                <CardHeader>
                    <CardTitle>Run Metadata</CardTitle>
                    <CardDescription>
                        Hardware and environment details
                    </CardDescription>
                </CardHeader>
                <CardContent>
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
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-col items-stretch space-y-0 border-b p-0 sm:flex-row">
                    <div className="flex flex-1 flex-col justify-center gap-1 px-6 py-5 sm:py-6">
                        <div className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Emissions Time Series</CardTitle>
                                <CardDescription>
                                    Showing emissions rate and energy consumed
                                    over time
                                </CardDescription>
                            </div>
                            {!isPublicView && (
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
                            )}
                        </div>
                    </div>
                    <div className="flex">
                        {Object.keys(chartConfig).map((key) => {
                            const chart = key as keyof typeof chartConfig;
                            return (
                                <button
                                    key={chart}
                                    data-active={activeChart === chart}
                                    className="flex flex-1 flex-col justify-center gap-1 border-t px-6 py-4 text-left even:border-l data-[active=true]:bg-muted/50 sm:border-l sm:border-t-0 sm:px-8 sm:py-6"
                                    onClick={() => setActiveChart(chart)}
                                >
                                    <span className="text-xs text-muted-foreground">
                                        {chartConfig[chart].label}
                                    </span>
                                </button>
                            );
                        })}
                    </div>
                </CardHeader>
                <CardContent className="px-2 sm:p-6">
                    <ChartContainer
                        config={chartConfig}
                        className="aspect-auto h-[250px] w-full"
                    >
                        <LineChart
                            data={emissionTimeSeries.emissions}
                            margin={{
                                left: 12,
                                right: 12,
                            }}
                        >
                            <CartesianGrid vertical={false} />
                            <XAxis
                                dataKey="timestamp"
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                                minTickGap={32}
                                tickFormatter={(value) => {
                                    const date = new Date(value);
                                    return date.toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                    });
                                }}
                            />
                            <YAxis
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                            />
                            <ChartTooltip
                                content={
                                    <ChartTooltipContent
                                        className="w-[150px]"
                                        labelFormatter={(value) => {
                                            return new Date(
                                                value,
                                            ).toLocaleDateString("en-US", {
                                                month: "short",
                                                day: "numeric",
                                                year: "numeric",
                                            });
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
                </CardContent>
            </Card>
        </div>
    );
}
