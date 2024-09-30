"use client";

import * as React from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";

interface EmissionsTimeSeriesChartProps {
    runId: string;
}

const chartConfig = {
    emissions_rate: {
        label: "Emissions Rate",
        color: "hsl(var(--chart-1))",
    },
    energy_consumed: {
        label: "Energy Consumed",
        color: "hsl(var(--chart-2))",
    },
} satisfies ChartConfig;

export default function EmissionsTimeSeriesChart({ runId }: EmissionsTimeSeriesChartProps) {
    const [activeChart, setActiveChart] = React.useState<keyof typeof chartConfig>("emissions_rate");
    const [emissionTimeSeries, setEmissionTimeSeries] = React.useState<EmissionsTimeSeries | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        async function fetchData() {
            setIsLoading(true);
            try {
                const data = await getEmissionsTimeSeries(runId);
                // Multiply the values by 1000 for demo purposes
                const multipliedData = {
                    ...data,
                    emissions: data.emissions.map(item => ({
                        ...item,
                        emissions_rate: item.emissions_rate * 1000,
                        energy_consumed: item.energy_consumed * 1000
                    }))
                };
                setEmissionTimeSeries(multipliedData);
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

    if (!emissionTimeSeries) {
        return <div>No data available</div>;
    }

    return (
        <Card>
            <CardHeader className="flex flex-col items-stretch space-y-0 border-b p-0 sm:flex-row">
                <div className="flex flex-1 flex-col justify-center gap-1 px-6 py-5 sm:py-6">
                    <CardTitle>Emissions Time Series</CardTitle>
                    <CardDescription>
                        Showing emissions rate and energy consumed over time
                    </CardDescription>
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
                                        return new Date(value).toLocaleDateString("en-US", {
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
    );
}

async function getEmissionsTimeSeries(runId: string): Promise<EmissionsTimeSeries> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/runs/${runId}/emissions`);
    if (!response.ok) {
        throw new Error('Failed to fetch emissions data');
    }
    return await response.json();
}