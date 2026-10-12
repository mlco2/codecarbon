import { RunReport } from "@/api/schemas";
import { format } from "date-fns";
import { Label, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { getRunEmissionsByExperiment } from "@/api/runs";
import { exportRunsToCsv } from "@/utils/export";
import { pickTimeFormat } from "@/helpers/time-axis";
import { useEffect, useMemo, useState } from "react";
import ChartSkeleton from "./chart-skeleton";
import { ExportCsvButton } from "./export-csv-button";
import { ChartConfig, ChartContainer } from "./ui/chart";

interface RunsScatterChartProps {
    isPublicView: boolean;
    params: {
        experimentId: string;
        startDate: string;
        endDate: string;
    };
    onRunClick: (runId: string) => void;
    projectName: string;
    experimentName?: string;
}

const chartConfig = {
    desktop: {
        label: "Emissions",
        color: "hsl(var(--primary))",
    },
    mobile: {
        label: "Energy consumed",
        color: "hsl(var(--secondary))",
    },
} satisfies ChartConfig;

export default function RunsScatterChart({
    isPublicView,
    params,
    onRunClick,
    projectName,
    experimentName,
}: RunsScatterChartProps) {
    const [runsReportsData, setExperimentsReportData] = useState<RunReport[]>(
        [],
    );
    const [isLoading, setIsLoading] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    useEffect(() => {
        if (!params.experimentId) {
            setExperimentsReportData([]);
            return;
        }
        let cancelled = false;
        setIsLoading(true);
        (async () => {
            try {
                const data = await getRunEmissionsByExperiment(
                    params.experimentId,
                    params.startDate,
                    params.endDate,
                );
                if (cancelled) return;
                const sortedData = data.sort(
                    (a, b) =>
                        new Date(a.timestamp).getTime() -
                        new Date(b.timestamp).getTime(),
                );
                setExperimentsReportData(sortedData);
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [params.experimentId, params.startDate, params.endDate]);

    // Add this custom tooltip function
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="custom-tooltip bg-background text-foreground p-2 border border-border rounded shadow">
                    <p>
                        <strong>Emissions:</strong> {data.emissions.toFixed(2)}{" "}
                        kgeqCO2
                    </p>
                    <p>
                        <strong>Energy Consumed:</strong>{" "}
                        {data.energy_consumed.toFixed(2)} kWh
                    </p>
                    <p>
                        <strong>Duration:</strong> {data.duration.toFixed(2)} s
                    </p>
                </div>
            );
        }
        return null;
    };

    const points = useMemo(
        () =>
            runsReportsData.map((r) => ({
                ...r,
                ts: new Date(r.timestamp).getTime(),
            })),
        [runsReportsData],
    );
    const tickFmt = useMemo(() => {
        if (points.length < 2) return "MMM d, HH:mm";
        return pickTimeFormat(points[points.length - 1].ts - points[0].ts);
    }, [points]);

    if (isLoading) {
        return <ChartSkeleton height={300} />;
    }

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>Scatter Chart - Emissions by Run Id</CardTitle>
                    <CardDescription>
                        Click a run to see time series
                    </CardDescription>
                </div>
                {!isPublicView && (
                    <ExportCsvButton
                        loadingMessage="Exporting runs..."
                        successMessage="Runs exported successfully"
                        errorMessage="Failed to export runs"
                        isDisabled={
                            isExporting ||
                            !params.experimentId ||
                            runsReportsData.length === 0
                        }
                        onDownload={async () => {
                            setIsExporting(true);
                            await exportRunsToCsv(
                                runsReportsData,
                                projectName,
                                experimentName,
                            );
                            setIsExporting(false);
                        }}
                    />
                )}
            </CardHeader>
            <CardContent>
                <ChartContainer config={chartConfig}>
                    {runsReportsData.length > 0 ? (
                        <ScatterChart
                            width={500}
                            height={300}
                            margin={{
                                top: 20,
                                right: 20,
                                bottom: 20,
                                left: 20,
                            }}
                        >
                            <XAxis
                                dataKey="ts"
                                name="Timestamp"
                                type="number"
                                scale="time"
                                domain={["dataMin", "dataMax"]}
                                stroke="currentColor"
                                minTickGap={48}
                                tickFormatter={(value) =>
                                    format(new Date(value), tickFmt)
                                }
                            >
                                <Label
                                    value="Timestamp"
                                    offset={-10}
                                    position="insideBottom"
                                    style={{ fill: "currentColor" }}
                                />
                            </XAxis>
                            <YAxis
                                dataKey="emissions"
                                name="Emissions"
                                type="number"
                                stroke="currentColor"
                            >
                                <Label
                                    value="Emissions (kg eq CO2)"
                                    angle={-90}
                                    position="insideLeft"
                                    style={{ fill: "currentColor" }}
                                />
                            </YAxis>
                            <Tooltip content={<CustomTooltip />} />
                            <Scatter
                                name="Emissions"
                                data={points}
                                fill="hsl(var(--primary))"
                                onClick={(data) => onRunClick(data.runId)}
                                cursor="pointer"
                            />
                        </ScatterChart>
                    ) : (
                        <div className="flex items-center justify-center h-full">
                            <p className="text-muted-foreground text-sm">
                                No data available
                            </p>
                        </div>
                    )}
                </ChartContainer>
            </CardContent>
        </Card>
    );
}
