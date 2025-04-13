import { DateRangePicker } from "@/components/date-range-picker";
import EmissionsTimeSeriesChart from "@/components/emissions-time-series";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RadialChart from "@/components/radial-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import { Separator } from "@/components/ui/separator";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { ExperimentReport } from "@/types/experiment-report";
import { Project } from "@/types/project";
import { ConvertedValues, RadialChartData } from "@/types/project-dashboard";
import Image from "next/image";
import { ReactNode, useState } from "react";
import { DateRange } from "react-day-picker";
import ChartSkeleton from "./chart-skeleton";
import CreateExperimentModal from "./createExperimentModal";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Skeleton } from "./ui/skeleton";
import { useRouter } from "next/navigation";
import { Table, TableBody, TableHeader } from "./ui/table";
import { Experiment } from "@/types/experiment";

export interface ProjectDashboardBaseProps {
    isPublicView: boolean;
    project: Project;
    date: DateRange;
    onDateChange: (newDate: DateRange | undefined) => void;
    radialChartData: RadialChartData;
    convertedValues: ConvertedValues;
    experimentsReportData: ExperimentReport[];
    projectExperiments: Experiment[];
    runData: {
        experimentId: string;
        startDate: string;
        endDate: string;
    };
    selectedExperimentId: string;
    selectedRunId: string;
    onExperimentClick: (experimentId: string) => void;
    onRunClick: (runId: string) => void;
    headerContent?: ReactNode;
    isLoading?: boolean;
}

export default function ProjectDashboardBase({
    isPublicView,
    project,
    date,
    onDateChange,
    radialChartData,
    convertedValues,
    experimentsReportData,
    projectExperiments,
    runData,
    selectedExperimentId,
    selectedRunId,
    onExperimentClick,
    onRunClick,
    headerContent,
    isLoading = false,
}: ProjectDashboardBaseProps) {
    const router = useRouter();
    const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

    const handleCreateExperimentClick = () => {
        setIsExperimentModalOpen(true);
    };

    const refreshExperimentList = async () => {
        router.refresh();
    };

    const experimentName = experimentsReportData.find(
        (experiment) => experiment.experiment_id === selectedExperimentId,
    )?.name;

    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                {headerContent ? (
                    headerContent
                ) : (
                    <div className="flex flex-col gap-2">
                        <h1 className="text-3xl font-bold">{project.name}</h1>
                        <p className="text-muted-foreground">
                            {project.description}
                        </p>
                    </div>
                )}
                <div>
                    <DateRangePicker
                        date={date}
                        onDateChange={(newDate) =>
                            onDateChange(newDate || getDefaultDateRange())
                        }
                    />
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
                <div className="grid grid-cols-1 gap-4">
                    {isLoading ? (
                        <>
                            <Skeleton className="h-20 w-full" />
                            <Skeleton className="h-20 w-full" />
                            <Skeleton className="h-20 w-full" />
                        </>
                    ) : (
                        <>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="flex items-center justify-center">
                                    <Image
                                        src="/icons/household_consumption.svg"
                                        alt="Household consumption icon"
                                        width={64}
                                        height={64}
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex flex-col col-span-2 justify-center">
                                    <p className="text-4xl text-primary">
                                        {convertedValues.citizen} %
                                    </p>
                                    <p className="text-sm font-medium">
                                        Of a U.S citizen weekly energy emissions
                                    </p>
                                </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="flex items-center justify-center">
                                    <Image
                                        src="/icons/transportation.svg"
                                        alt="Transportation icon"
                                        width={64}
                                        height={64}
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex flex-col col-span-2 justify-center">
                                    <p className="text-4xl text-primary">
                                        {convertedValues.transportation}
                                    </p>
                                    <p className="text-sm font-medium">
                                        Kilometers ridden
                                    </p>
                                </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="flex items-center justify-center">
                                    <Image
                                        src="/icons/tv.svg"
                                        alt="TV icon"
                                        width={64}
                                        height={64}
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex flex-col col-span-2 justify-center">
                                    <p className="text-4xl text-primary">
                                        {convertedValues.tvTime} days
                                    </p>
                                    <p className="text-sm font-medium">
                                        Of watching TV
                                    </p>
                                </div>
                            </div>
                        </>
                    )}
                </div>
                <div className="col-span-1 items-center justify-center w-full h-full">
                    {isLoading ? (
                        <Card className="flex flex-col h-full items-center justify-center">
                            <CardContent className="p-0">
                                <Skeleton className="h-44 w-44 rounded-full" />
                            </CardContent>
                        </Card>
                    ) : (
                        <RadialChart data={radialChartData.energy} />
                    )}
                </div>
                <div className="col-span-1 items-center justify-center w-full h-full">
                    {isLoading ? (
                        <Card className="flex flex-col h-full items-center justify-center">
                            <CardContent className="p-0">
                                <Skeleton className="h-44 w-44 rounded-full" />
                            </CardContent>
                        </Card>
                    ) : (
                        <RadialChart data={radialChartData.emissions} />
                    )}
                </div>
                <div className="col-span-1 items-center justify-center w-full h-full">
                    {isLoading ? (
                        <Card className="flex flex-col h-full items-center justify-center">
                            <CardContent className="p-0">
                                <Skeleton className="h-44 w-44 rounded-full" />
                            </CardContent>
                        </Card>
                    ) : (
                        <RadialChart data={radialChartData.duration} />
                    )}
                </div>
            </div>

            <Separator className="h-[0.5px] bg-muted-foreground my-6" />
            <Card className="flex flex-col md:flex-row justify-start gap-4 px-4 py-4 w-full max-w-3/4">
                <div className="flex items-center justify-start px-2">
                    <p className="text-sm font-medium pr-2 text-center">
                        {projectExperiments.length === 0
                            ? isPublicView
                                ? "No experiment data in the selected date range" // This is because for public projects we show only the experiments that have runs, but for private projects we show in this list as well the projects created but without runs yet
                                : "No experiments have been created yet."
                            : "Set of experiments included in this project"}
                    </p>
                    {!isPublicView && (
                        <div className="flex items-center justify-center px-2">
                            <Button
                                onClick={handleCreateExperimentClick}
                                className="bg-primary text-primary-foreground"
                            >
                                + Add Experiment
                            </Button>
                            <CreateExperimentModal
                                projectId={project.id}
                                isOpen={isExperimentModalOpen}
                                onClose={() => setIsExperimentModalOpen(false)}
                                onExperimentCreated={refreshExperimentList}
                            />
                        </div>
                    )}
                </div>
                {projectExperiments.length !== 0 && (
                    <Card className="flex flex-col md:flex-row justify-between md:items-center gap-4 py-4 px-4 w-full max-w-3/4">
                        <Table>
                            <TableHeader>
                                <tr>
                                    <th className="text-left">Experiment</th>
                                    <th className="text-left">Description</th>
                                    {!isPublicView && (
                                        <th className="text-left">
                                            Experiment id
                                        </th>
                                    )}
                                </tr>
                            </TableHeader>
                            <TableBody>
                                {projectExperiments.map((experiment) => (
                                    <tr
                                        key={experiment.id}
                                        className={`cursor-pointer hover:bg-muted/50 ${
                                            experiment.id ===
                                            selectedExperimentId
                                                ? "bg-primary/10"
                                                : ""
                                        }`}
                                        onClick={() =>
                                            onExperimentClick(
                                                experiment.id || "",
                                            )
                                        }
                                    >
                                        <td>{experiment.name}</td>
                                        <td>{experiment.description}</td>
                                        {!isPublicView && (
                                            <td>{experiment.id}</td>
                                        )}
                                    </tr>
                                ))}
                            </TableBody>
                        </Table>
                    </Card>
                )}
            </Card>
            <div className="grid gap-8 md:grid-cols-2">
                {isLoading ? (
                    <>
                        <ChartSkeleton height={300} />
                        <ChartSkeleton height={300} />
                    </>
                ) : (
                    <>
                        <ExperimentsBarChart
                            isPublicView={isPublicView}
                            experimentsReportData={experimentsReportData}
                            onExperimentClick={onExperimentClick}
                            projectName={project.name}
                            selectedExperimentId={selectedExperimentId}
                        />
                        <RunsScatterChart
                            isPublicView={isPublicView}
                            params={{
                                ...runData,
                                experimentId: selectedExperimentId,
                            }}
                            onRunClick={onRunClick}
                            projectName={project.name}
                            experimentName={experimentName}
                        />
                    </>
                )}
            </div>
            {selectedRunId && selectedRunId != "" && (
                <>
                    <Separator className="h-[0.5px] bg-muted-foreground my-6" />
                    <div className="w-full">
                        {isLoading ? (
                            <ChartSkeleton height={350} />
                        ) : (
                            <EmissionsTimeSeriesChart
                                isPublicView={isPublicView}
                                runId={selectedRunId}
                                projectName={project.name}
                                experimentName={experimentName}
                            />
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
