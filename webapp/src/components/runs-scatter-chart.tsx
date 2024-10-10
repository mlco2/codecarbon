import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, Label } from "recharts";
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

interface RunsScatterChartProps {
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
    const url = `${process.env.NEXT_PUBLIC_API_URL}/experiments/${experimentId}/runs/sums?start_date=${startDate}&end_date=${endDate}`;

    const res = await fetch(url);

    if (!res.ok) {
        // Log error waiting for a better error management
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

export default function RunsScatterChart({
    params,
    onRunClick,
}: RunsScatterChartProps) {
    const [runsReportsData, setExperimentsReportData] = useState<RunReport[]>(
        [],
    );
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

    // Add this custom tooltip function
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
                <CardTitle>Scatter Chart - Emissions by Run Id</CardTitle>
                <CardDescription></CardDescription>
            </CardHeader>
            <CardContent>
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
                        tickFormatter={(timestamp) =>
                            format(new Date(timestamp), "MM/dd/yyyy")
                        }
                    >
                        <Label
                            value="Timestamp"
                            offset={0}
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
                            value="Emissions"
                            angle={-90}
                            position="insideLeft"
                            style={{ fill: "currentColor" }}
                        />
                    </YAxis>
                    <Tooltip content={<CustomTooltip />} />
                    <Scatter
                        name="Emissions"
                        data={runsReportsData}
                        fill="hsl(var(--primary)))"
                        onClick={(data) => onRunClick(data.runId)}
                        cursor="pointer"
                    />
                </ScatterChart>
            </CardContent>
        </Card>
    );
}
