"use client";

import { TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";
import { ExperimentReport } from "@/types/experiment-report";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";

async function getProjectEmissionsByExperiment(
    projectId: string,
): Promise<ExperimentReport[]> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/experiments/sums/`,
    );

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }
    const result = await res.json();
    return result.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            name: experimentReport.name,
            emissions: experimentReport.emissions*1000,
            energy_consumed: experimentReport.energy_consumed*1000,
        };
    });
}

const chartConfig = {
    desktop: {
        label: "Emissions",
        color: "hsl(var(--chart-1))",
    },
    mobile: {
        label: "Energy consumed",
        color: "hsl(var(--chart-2))",
    },
} satisfies ChartConfig;

type Params = {
    projectId: string;
};
export default async function ExperimentsBarChart({
    params,
}: Readonly<{ params: Params }>) {
    const experimentsReportData = await getProjectEmissionsByExperiment(
        params.projectId,
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
                        />
                        <Bar
                            dataKey="energy_consumed"
                            fill="var(--color-mobile)"
                            radius={4}
                        />
                    </BarChart>
                </ChartContainer>
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
                <div className="flex gap-2 font-medium leading-none">
                    Trending up by 5.2% this month{" "}
                    <TrendingUp className="h-4 w-4" />
                </div>
                <div className="leading-none text-muted-foreground">
                    Showing total visitors for the last 6 months
                </div>
            </CardFooter>
        </Card>
    );
}
