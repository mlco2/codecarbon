"use client";

import { ExperimentReport } from "@/types/experiment-report";
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";

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
import { exportExperimentsToCsv } from "@/utils/export";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { ExportCsvButton } from "./export-csv-button";

interface ExperimentsBarChartProps {
    isPublicView: boolean;
    experimentsReportData: ExperimentReport[];
    onExperimentClick: (experimentId: string) => void;
    selectedExperimentId: string;
    localLoading?: boolean;
    projectName: string;
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

export default function ExperimentsBarChart({
    isPublicView,
    experimentsReportData,
    onExperimentClick,
    selectedExperimentId,
    localLoading = false,
    projectName,
}: ExperimentsBarChartProps) {
    const [selectedBar, setSelectedBar] = useState(0);
    const [isExporting, setIsExporting] = useState(false);

    const handleBarClick = (data: ExperimentReport, index: number) => {
        onExperimentClick(data.experiment_id);
    };
    useEffect(() => {
        const highlightedBar = experimentsReportData.findIndex(
            (experiment) => experiment.experiment_id === selectedExperimentId,
        );
        setSelectedBar(highlightedBar);
    }, [selectedExperimentId, experimentsReportData]);

    const CustomBar = (props: any) => {
        const { fill, x, y, width, height, index } = props;
        const barFill =
            selectedBar === index
                ? "var(--color-desktop)"
                : "var(--color-mobile)";
        return (
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={barFill}
                onClick={() => handleBarClick(props.payload, index)}
                cursor="pointer"
            />
        );
    };
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>Project experiment runs</CardTitle>
                    <CardDescription>
                        Click an experiment to see the runs on the chart on the
                        right
                    </CardDescription>
                </div>
                {!isPublicView && (
                    <ExportCsvButton
                        isDisabled={
                            isExporting || experimentsReportData.length === 0
                        }
                        onDownload={async () => {
                            setIsExporting(true);
                            exportExperimentsToCsv(
                                experimentsReportData,
                                projectName,
                            );
                            setIsExporting(false);
                        }}
                        loadingMessage="Exporting experiments..."
                        successMessage="Experiments exported successfully"
                        errorMessage="Failed to export experiments"
                    />
                )}
            </CardHeader>
            <CardContent>
                {localLoading ? (
                    <div className="flex items-center justify-center h-[300px]">
                        <Loader2 className="h-16 w-16 animate-spin text-primary" />
                    </div>
                ) : (
                    <ChartContainer config={chartConfig}>
                        {experimentsReportData.length > 0 ? (
                            <BarChart
                                accessibilityLayer
                                data={experimentsReportData}
                            >
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
                                    content={
                                        <ChartTooltipContent indicator="dashed" />
                                    }
                                />
                                <Bar
                                    dataKey="emissions"
                                    shape={<CustomBar />}
                                    radius={4}
                                />
                            </BarChart>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-sm text-muted-foreground">
                                    No data available
                                </p>
                            </div>
                        )}
                    </ChartContainer>
                )}
            </CardContent>
        </Card>
    );
}
