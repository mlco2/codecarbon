import { DateRangePicker } from "@/components/date-range-picker";
import { Separator } from "@/components/ui/separator";
import { getDefaultDateRange } from "@/helpers/date-utils";
import {
    ExperimentReport,
    Project,
    ConvertedValues,
    RadialChartData,
    Experiment,
} from "@/api/schemas";
import { lazy, ReactNode, Suspense, useState } from "react";
import { DateRange } from "react-day-picker";
import ChartSkeleton from "./chart-skeleton";
import CreateExperimentModal from "./createExperimentModal";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "./ui/select";
import { Skeleton } from "./ui/skeleton";
import { Copy } from "lucide-react";
import { toast } from "sonner";

// Sentinel value for the "show data from every experiment" option in the
// experiment dropdown. Radix Select forbids an empty string as an item value.
const ALL_EXPERIMENTS = "__all__";

const RadialChart = lazy(() => import("@/components/radial-chart"));
const ExperimentsBarChart = lazy(
    () => import("@/components/experiment-bar-chart"),
);
const RunsScatterChart = lazy(() => import("@/components/runs-scatter-chart"));
const EmissionsTimeSeriesChart = lazy(
    () => import("@/components/emissions-time-series"),
);

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
    onExperimentCreated?: () => void;
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
    onExperimentCreated,
    headerContent,
    isLoading = false,
}: ProjectDashboardBaseProps) {
    const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

    const handleCreateExperimentClick = () => {
        setIsExperimentModalOpen(true);
    };

    const experimentName = experimentsReportData.find(
        (experiment) => experiment.experiment_id === selectedExperimentId,
    )?.name;

    const selectedExperiment = projectExperiments.find(
        (e) => e.id === selectedExperimentId,
    );

    const handleSelectExperiment = (value: string) => {
        onExperimentClick(value === ALL_EXPERIMENTS ? "" : value);
    };

    const handleCopyExperimentId = async (id: string) => {
        try {
            await navigator.clipboard.writeText(id);
            toast.success("Experiment id copied");
        } catch {
            toast.error("Failed to copy");
        }
    };

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
                                    <img
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
                                    <img
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
                                    <img
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
                        <Suspense
                            fallback={
                                <Card className="flex flex-col h-full items-center justify-center">
                                    <CardContent className="p-0">
                                        <Skeleton className="h-44 w-44 rounded-full" />
                                    </CardContent>
                                </Card>
                            }
                        >
                            <RadialChart data={radialChartData.energy} />
                        </Suspense>
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
                        <Suspense
                            fallback={
                                <Card className="flex flex-col h-full items-center justify-center">
                                    <CardContent className="p-0">
                                        <Skeleton className="h-44 w-44 rounded-full" />
                                    </CardContent>
                                </Card>
                            }
                        >
                            <RadialChart data={radialChartData.emissions} />
                        </Suspense>
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
                        <Suspense
                            fallback={
                                <Card className="flex flex-col h-full items-center justify-center">
                                    <CardContent className="p-0">
                                        <Skeleton className="h-44 w-44 rounded-full" />
                                    </CardContent>
                                </Card>
                            }
                        >
                            <RadialChart data={radialChartData.duration} />
                        </Suspense>
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
                                onExperimentCreated={onExperimentCreated}
                            />
                        </div>
                    )}
                </div>
                {projectExperiments.length !== 0 && (
                    <div className="flex flex-col gap-3 w-full md:w-2/3">
                        <Select
                            value={selectedExperimentId || ALL_EXPERIMENTS}
                            onValueChange={handleSelectExperiment}
                        >
                            <SelectTrigger
                                data-testid="experiment-select"
                                aria-label="Select an experiment"
                            >
                                <SelectValue placeholder="Select an experiment" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value={ALL_EXPERIMENTS}>
                                    All experiments
                                </SelectItem>
                                {projectExperiments.map((experiment) => (
                                    <SelectItem
                                        key={experiment.id}
                                        value={experiment.id}
                                        data-testid={`experiment-option-${experiment.id}`}
                                    >
                                        {experiment.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        {selectedExperiment && (
                            <Card
                                className="p-4 flex flex-col gap-2"
                                data-testid="experiment-details"
                            >
                                {selectedExperiment.description && (
                                    <p className="text-sm text-muted-foreground">
                                        {selectedExperiment.description}
                                    </p>
                                )}
                                {!isPublicView && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-medium text-muted-foreground">
                                            Experiment id
                                        </span>
                                        <code className="text-xs bg-muted px-2 py-1 rounded font-mono break-all">
                                            {selectedExperiment.id}
                                        </code>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7"
                                            aria-label="Copy experiment id"
                                            onClick={() =>
                                                handleCopyExperimentId(
                                                    selectedExperiment.id,
                                                )
                                            }
                                        >
                                            <Copy className="h-4 w-4" />
                                        </Button>
                                    </div>
                                )}
                            </Card>
                        )}
                    </div>
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
                        <Suspense fallback={<ChartSkeleton height={300} />}>
                            <ExperimentsBarChart
                                isPublicView={isPublicView}
                                experimentsReportData={experimentsReportData}
                                onExperimentClick={onExperimentClick}
                                projectName={project.name}
                                selectedExperimentId={selectedExperimentId}
                            />
                        </Suspense>
                        <Suspense fallback={<ChartSkeleton height={300} />}>
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
                        </Suspense>
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
                            <Suspense fallback={<ChartSkeleton height={350} />}>
                                <EmissionsTimeSeriesChart
                                    isPublicView={isPublicView}
                                    runId={selectedRunId}
                                    projectName={project.name}
                                    experimentName={experimentName}
                                />
                            </Suspense>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
