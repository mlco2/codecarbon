import { DateRangePicker } from "@/components/date-range-picker";
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
import ChartRow from "./chart-row";
import ChartSkeleton from "./chart-skeleton";
import ConsumedEnergyGauges from "./consumed-energy-gauges";
import { PlusIcon } from "./icons/plus-icon";
import { PrimaryButton } from "./ui/primary-button";
import EquivalenceList, { equivalences } from "./equivalence-list";
import CreateExperimentModal from "./create-experiment-modal";
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
        /*
         * No gap on this column: the charts below are separated by rules that have
         * to meet, and a gap here would push the horizontal one away from the
         * vertical ones. Each block carries its own space instead.
         */
        <div className="flex flex-col">
            <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center">
                {headerContent}
                <div className="w-full max-w-sm md:ml-auto">
                    <DateRangePicker
                        variant="dashboard"
                        date={date}
                        onDateChange={(newDate) =>
                            onDateChange(newDate || getDefaultDateRange())
                        }
                    />
                </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-8 lg:gap-12">
                {isLoading ? (
                    <div className="flex min-w-64 flex-1 flex-col gap-6 lg:gap-8">
                        <Skeleton className="h-[50px] w-full" />
                        <Skeleton className="h-[50px] w-full" />
                        <Skeleton className="h-[50px] w-full" />
                    </div>
                ) : (
                    <EquivalenceList
                        direction="column"
                        items={equivalences(convertedValues)}
                        className="min-w-64 flex-1"
                    />
                )}

                <section className="flex min-w-0 flex-col gap-6 lg:gap-heading">
                    <h2 className="type-display type-section-title text-cc-white">
                        Consumed energy
                    </h2>
                    {isLoading ? (
                        <div className="flex flex-wrap gap-6 lg:gap-9">
                            <Skeleton className="size-40 rounded-full sm:size-gauge" />
                            <Skeleton className="size-40 rounded-full sm:size-gauge" />
                            <Skeleton className="size-40 rounded-full sm:size-gauge" />
                        </div>
                    ) : (
                        <ConsumedEnergyGauges
                            gauges={[
                                radialChartData.energy,
                                radialChartData.emissions,
                                radialChartData.duration,
                            ]}
                        />
                    )}
                </section>
            </div>

            <section className="mt-6 flex flex-col gap-6 border-t border-cc-rule pt-6 lg:pt-8">
                <h2 className="type-display type-section-title text-cc-white">
                    Experiments
                </h2>

                {projectExperiments.length === 0 && (
                    <p className="type-mono-medium type-field text-cc-white">
                        {isPublicView
                            ? // Public projects list only experiments that have
                              // runs; private ones also list those created without
                              // any runs yet.
                              "No experiment data in the selected date range"
                            : "No experiments have been created yet."}
                    </p>
                )}

                <div className="flex flex-col items-start gap-4 md:flex-row">
                    {projectExperiments.length !== 0 && (
                        <div className="flex w-full flex-col gap-3 md:max-w-md">
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
                                <div
                                    className="flex flex-col gap-3 rounded-field bg-white/5 px-4 py-3"
                                    data-testid="experiment-details"
                                >
                                    {selectedExperiment.description && (
                                        <p className="type-mono-medium type-row-meta break-words text-cc-white">
                                            {selectedExperiment.description}
                                        </p>
                                    )}
                                    {!isPublicView && (
                                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                                            <span className="type-mono-medium type-row-meta text-cc-gray">
                                                Experiment id
                                            </span>
                                            <code className="type-mono-regular type-row-meta min-w-0 break-all text-cc-text-input-gray">
                                                {selectedExperiment.id}
                                            </code>
                                            <button
                                                type="button"
                                                aria-label="Copy experiment id"
                                                onClick={() =>
                                                    handleCopyExperimentId(
                                                        selectedExperiment.id,
                                                    )
                                                }
                                                className="cursor-pointer text-cc-gray outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime motion-reduce:transition-none"
                                            >
                                                <Copy className="size-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {!isPublicView && (
                        <>
                            <PrimaryButton
                                onClick={handleCreateExperimentClick}
                                ringOffset="page"
                                className="h-control shrink-0 gap-1"
                            >
                                <PlusIcon className="size-5 shrink-0" />
                                Add an experiment
                            </PrimaryButton>
                            <CreateExperimentModal
                                projectId={project.id}
                                isOpen={isExperimentModalOpen}
                                onClose={() => setIsExperimentModalOpen(false)}
                                onExperimentCreated={onExperimentCreated}
                            />
                        </>
                    )}
                </div>
            </section>
            <ChartRow insetBottom className="mt-6 lg:mt-10">
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
            </ChartRow>
            {selectedRunId && selectedRunId != "" && (
                <div className="w-full border-t border-cc-rule">
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
            )}
        </div>
    );
}
