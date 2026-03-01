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
import { useEffect, useState } from "react";
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
    const [isExporting, setIsExporting] = useState(false);
    useEffect(() => {
        const fetchData = async () => {
            const data = await getRunEmissionsByExperiment(
                params.experimentId,
                params.startDate,
                params.endDate,
            );
            // Sort the data by timestamp
            const sortedData = data.sort(
                (a, b) =>
                    new Date(a.timestamp).getTime() -
                    new Date(b.timestamp).getTime(),
            );
            setExperimentsReportData(sortedData);
        };
        fetchData();
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
                                dataKey="timestamp"
                                name="Timestamp"
                                type="category"
                                stroke="currentColor"
                                tickFormatter={(value) =>
                                    format(new Date(value), "yyyy-MM-dd HH:mm")
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
                                data={runsReportsData}
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
