"use client";

import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";
import { ExperimentReport } from "@/types/experiment-report";

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

interface ExperimentsBarChartProps {
    params: {
        projectId: string;
        startDate: string;
        endDate: string;
    };
    onExperimentClick: (experimentId: string) => void;
}

async function getProjectEmissionsByExperiment(
    projectId: string,
    startDate: string,
    endDate: string,
): Promise<ExperimentReport[]> {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/experiments/sums?start_date=${startDate}&end_date=${endDate}`;

    const res = await fetch(url);

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }
    const result = await res.json();
    return result.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            name: experimentReport.name,
            emissions: experimentReport.emissions * 1000,
            energy_consumed: experimentReport.energy_consumed * 1000,
        };
    });
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

type Params = {
    projectId: string;
    startDate: string;
    endDate: string;
};
export default async function ExperimentsBarChart({
    params,
    onExperimentClick,
}: ExperimentsBarChartProps) {
    const experimentsReportData = await getProjectEmissionsByExperiment(
        params.projectId,
        params.startDate,
        params.endDate,
    );
    return (
        <Card>
            <CardHeader>
                <CardTitle>Project experiment runs</CardTitle>
                <CardDescription>January - June 2024</CardDescription>
            </CardHeader>
            <CardContent>
                <ChartContainer config={chartConfig}>
                    <BarChart accessibilityLayer data={experimentsReportData}>
                        <CartesianGrid vertical={false} />
                        <XAxis
                            dataKey="name"
                            tickLine={false}
                            tickMargin={10}
                            axisLine={false}
                            tickFormatter={(value) => value.slice(0, 3)}
                        />
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent indicator="dashed" />}
                        />
                        <Bar
                            dataKey="emissions"
                            fill="var(--color-desktop)"
                            radius={4}
                            onClick={(data) =>
                                onExperimentClick(data.experiment_id)
                            }
                            cursor="pointer"
                        />
                    </BarChart>
                </ChartContainer>
            </CardContent>
        </Card>
    );
}
