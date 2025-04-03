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
import { Emission } from "@/types/emission";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";
import { RunMetadata } from "@/types/run-metadata";
import * as React from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { fetchApi } from "@/utils/api";
import { Cpu, HardDrive, Server } from "lucide-react";

interface EmissionsTimeSeriesChartProps {
    runId: string;
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
    runId,
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

    if (!emissionTimeSeries) {
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

async function getEmissionsTimeSeries(
    runId: string,
): Promise<EmissionsTimeSeries> {
    try {
        const runMetadataData = await fetchApi<RunMetadata>(`/runs/${runId}`);
        const emissionsData = await fetchApi<{ items: Emission[] }>(
            `/runs/${runId}/emissions`,
        );

        const metadata: RunMetadata = {
            timestamp: runMetadataData.timestamp,
            experiment_id: runMetadataData.experiment_id,
            os: runMetadataData.os,
            python_version: runMetadataData.python_version,
            codecarbon_version: runMetadataData.codecarbon_version,
            cpu_count: runMetadataData.cpu_count,
            cpu_model: runMetadataData.cpu_model,
            gpu_count: runMetadataData.gpu_count,
            gpu_model: runMetadataData.gpu_model,
            longitude: runMetadataData.longitude,
            latitude: runMetadataData.latitude,
            region: runMetadataData.region,
            provider: runMetadataData.provider,
            ram_total_size: runMetadataData.ram_total_size,
            tracking_mode: runMetadataData.tracking_mode,
        };

        const emissions: Emission[] = emissionsData.items.map((item: any) => ({
            emission_id: item.run_id,
            timestamp: item.timestamp,
            emissions_sum: item.emissions_sum,
            emissions_rate: item.emissions_rate,
            cpu_power: item.cpu_power,
            gpu_power: item.gpu_power,
            ram_power: item.ram_power,
            cpu_energy: item.cpu_energy,
            gpu_energy: item.gpu_energy,
            ram_energy: item.ram_energy,
            energy_consumed: item.energy_consumed,
        }));

        return {
            runId,
            emissions,
            metadata,
        };
    } catch (error) {
        console.error("Failed to fetch emissions time series:", error);
        throw error;
    }
}
