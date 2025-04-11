"use client";

import { TrendingUp } from "lucide-react";
import {
    Label,
    PolarGrid,
    PolarRadiusAxis,
    RadialBar,
    RadialBarChart,
} from "recharts";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { ChartConfig, ChartContainer } from "@/components/ui/chart";

export const description = "A radial chart with a custom shape";
type chartDataType = {
    label: string;
    value: number;
};

export default function RadialChart({
    data,
}: Readonly<{ data: chartDataType }>) {
    const chartConfig = {
        value: {
            label: data?.label || "",
            color: "hsl(var(--primary))",
        },
    } satisfies ChartConfig;

    // Check if data is missing or empty
    if (!data || data.value === undefined) {
        return (
            <Card className="flex flex-col">
                <CardContent className="flex-1 pb-0 flex items-center justify-center">
                    <div className="text-muted-foreground text-lg h-[250px] flex items-center">
                        No data available
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="flex flex-col">
            <CardContent className="flex-1 pb-0">
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square max-h-[250px]"
                >
                    <RadialBarChart
                        data={[data]}
                        endAngle={100}
                        innerRadius={80}
                        outerRadius={140}
                    >
                        <PolarGrid
                            gridType="circle"
                            radialLines={false}
                            stroke="none"
                            className="first:fill-muted last:fill-background"
                            polarRadius={[86, 74]}
                        />
                        <RadialBar dataKey="value" background />
                        <PolarRadiusAxis
                            tick={false}
                            tickLine={false}
                            axisLine={false}
                        >
                            <Label
                                content={({ viewBox }) => {
                                    if (
                                        viewBox &&
                                        "cx" in viewBox &&
                                        "cy" in viewBox
                                    ) {
                                        return (
                                            <text
                                                x={viewBox.cx}
                                                y={viewBox.cy}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={viewBox.cy}
                                                    className="fill-primary text-4xl font-bold"
                                                >
                                                    {data.value}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + 24}
                                                    className="text-xl"
                                                    style={{
                                                        fill: "hsl(var(--card-foreground))",
                                                    }}
                                                >
                                                    {data.label}
                                                </tspan>
                                            </text>
                                        );
                                    }
                                }}
                            />
                        </PolarRadiusAxis>
                    </RadialBarChart>
                </ChartContainer>
            </CardContent>
        </Card>
    );
}
