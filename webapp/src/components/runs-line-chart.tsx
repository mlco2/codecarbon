import {
    CartesianGrid,
    Line,
    LineChart,
    XAxis,
    YAxis,
    Tooltip,
    Label,
} from "recharts";
import { format } from "date-fns";
import { RunReport } from "@/types/run-report";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { useState, useEffect } from "react";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "./ui/chart";

interface RunsLineChartProps {
    params: {
        experimentId: string;
        startDate: string;
        endDate: string;
    };
    onRunClick: (runId: string) => void;
}

async function getRunEmissionsByExperiment(
    experimentId: string,
    startDate: string,
    endDate: string,
): Promise<RunReport[]> {
    if (!experimentId || experimentId == "") {
        return [];
    }

    const url = `${process.env.NEXT_PUBLIC_API_URL}/experiments/${experimentId}/runs/sums?start_date=${startDate}&end_date=${endDate}`;
    const res = await fetch(url);

    if (!res.ok) {
        console.log("Failed to fetch data");
        return [];
    }
    const result = await res.json();
    return result.map((runReport: RunReport) => {
        return {
            runId: runReport.run_id,
            emissions: runReport.emissions * 1000,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed * 1000,
            duration: runReport.duration * 10,
        };
    });
}

const chartConfig = {
    emissions: {
        label: "Emissions",
        color: "hsl(var(--primary))",
    },
    energy_consumed: {
        label: "Energy Consumed",
        color: "hsl(var(--secondary))",
    },
} satisfies ChartConfig;

export default function RunsLineChart({
    params,
    onRunClick,
}: RunsLineChartProps) {
    const [runsReportsData, setExperimentsReportData] = useState<RunReport[]>([]);
    const [activeChart, setActiveChart] = useState<keyof typeof chartConfig>("emissions");

    useEffect(() => {
        const fetchData = async () => {
            console.log("Fetching runs report data");
            const data = await getRunEmissionsByExperiment(
                params.experimentId,
                params.startDate,
                params.endDate,
            );
            setExperimentsReportData(data);
        };
        fetchData();
    }, [params.experimentId, params.startDate, params.endDate]);

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="custom-tooltip bg-background text-foreground p-2 border border-border rounded shadow">
                    <p>
                        <strong>Emissions:</strong> {data.emissions.toFixed(2)}
                    </p>
                    <p>
                        <strong>Energy Consumed:</strong>{" "}
                        {data.energy_consumed.toFixed(2)}
                    </p>
                    <p>
                        <strong>Duration:</strong> {data.duration.toFixed(2)}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Time Series - Emissions by Run</CardTitle>
                <CardDescription>
                    Click a point to see time series
                </CardDescription>
            </CardHeader>
            <CardContent>
                <ChartContainer config={chartConfig}>
                    <LineChart data={runsReportsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                            dataKey="timestamp"
                            tickFormatter={(value) => format(new Date(value), "yyyy-MM-dd HH:mm")}
                        >
                            <Label
                                value="Timestamp"
                                offset={-10}
                                position="insideBottom"
                                style={{ fill: "currentColor" }}
                            />
                        </XAxis>
                        <YAxis>
                            <Label
                                value="Emissions"
                                angle={-90}
                                position="insideLeft"
                                style={{ fill: "currentColor" }}
                            />
                        </YAxis>
                        <Tooltip content={<CustomTooltip />} />
                        <Line 
                            type="monotone" 
                            dataKey={activeChart}
                            stroke={chartConfig[activeChart].color}
                            dot={{ 
                                r: 4,
                                cursor: 'pointer',
                                onClick: (data: any) => {
                                    if (data && data.payload) {
                                        onRunClick(data.payload.runId);
                                    }
                                }
                            }}
                        />
                    </LineChart>
                </ChartContainer>
            </CardContent>
        </Card>
    );
} 