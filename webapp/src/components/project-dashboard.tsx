import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import {
    getEmissionsTimeSeries,
    getRunEmissionsByExperiment,
} from "@/server-functions/runs";
import { ProjectDashboardProps } from "@/types/project-dashboard";
import { exportToJson } from "@/utils/export";
import { Download, LockIcon, SettingsIcon, Share2Icon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import ProjectDashboardBase from "./project-dashboard-base";
import ProjectSettingsModal from "./project-settings-modal";
import ShareProjectButton from "./share-project-button";

export default function ProjectDashboard({
    project,
    date,
    onDateChange,
    radialChartData,
    convertedValues,
    experimentsReportData,
    runData,
    selectedExperimentId,
    selectedRunId,
    onExperimentClick,
    onRunClick,
    onSettingsClick,
    isLoading,
}: ProjectDashboardProps) {
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
    const [isExporting, setIsExporting] = useState(false);

    const handleJsonExport = () => {
        if (isExporting) return;

        setIsExporting(true);

        toast.promise(
            (async () => {
                // Prepare the experiments data with runs for each experiment
                const experimentsWithRuns = await Promise.all(
                    experimentsReportData.map(async (exp) => {
                        // Fetch runs for each experiment
                        const runs = await getRunEmissionsByExperiment(
                            exp.experiment_id,
                            runData.startDate,
                            runData.endDate,
                        );

                        // Fetch metadata and emissions for each run
                        const runsWithDetails = await Promise.all(
                            runs.map(async (run) => {
                                // Get emissions time series data (includes metadata)
                                const emissionsData =
                                    await getEmissionsTimeSeries(run.runId);

                                // Return run with metadata and emissions
                                return {
                                    ...run,
                                    emissions_value: run.emissions,
                                    emissions:
                                        emissionsData?.emissions || undefined,
                                    metadata:
                                        emissionsData.metadata || undefined,
                                };
                            }),
                        );

                        // Return experiment data with its enhanced runs
                        return {
                            experiment_id: exp.experiment_id,
                            name: exp.name,
                            emissions: exp.emissions,
                            energy_consumed: exp.energy_consumed,
                            duration: exp.duration,
                            runs: runsWithDetails,
                        };
                    }),
                );

                // Format the project data according to the requested structure
                const formattedData = {
                    projects: [
                        {
                            // Include all project properties
                            id: project.id,
                            name: project.name,
                            description: project.description,
                            public: project.public,
                            organizationId: project.organizationId,
                            experiments: experimentsWithRuns,

                            // Add extra metadata
                            date_range: {
                                startDate: runData.startDate,
                                endDate: runData.endDate,
                            },
                        },
                    ],
                };

                exportToJson(formattedData);
                // Small delay to make the loading state visible
                await new Promise((resolve) => setTimeout(resolve, 500));
                setIsExporting(false);
            })(),
            {
                loading: "Exporting JSON data...",
                success: "JSON data exported successfully",
                error: "Failed to export JSON data",
            },
        );
    };

    const headerContent = (
        <div className="flex flex-row gap-6 items-center justify-between w-full">
            <div className="flex items-center gap-2">
                <h1 className="text-2xl font-semi-bold">
                    Project {project.name}
                </h1>
                {project.public !== undefined && (
                    <div className="ml-2">
                        <ProjectVisibilityBadge isPublic={project.public} />
                    </div>
                )}
            </div>
            <div className="flex items-center gap-2">
                <ShareProjectButton
                    projectId={project.id}
                    isPublic={project.public}
                />
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                className="p-1 rounded-full"
                                variant="outline"
                                size="icon"
                                onClick={handleJsonExport}
                                disabled={isExporting}
                            >
                                {isExporting ? (
                                    <Download className="h-5 w-5 animate-pulse" />
                                ) : (
                                    <Download className="h-5 w-5" />
                                )}
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Download JSON export</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <Button
                    className="p-1 rounded-full"
                    variant="outline"
                    size="icon"
                    onClick={() => setIsSettingsModalOpen(true)}
                >
                    <SettingsIcon className="h-5 w-5" />
                </Button>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col gap-4 p-4 md:gap-8 md:p-4">
            <ProjectDashboardBase
                isPublicView={false}
                project={project}
                date={date}
                onDateChange={onDateChange}
                radialChartData={radialChartData}
                convertedValues={convertedValues}
                experimentsReportData={experimentsReportData}
                runData={runData}
                selectedExperimentId={selectedExperimentId}
                selectedRunId={selectedRunId}
                onExperimentClick={onExperimentClick}
                onRunClick={onRunClick}
                headerContent={headerContent}
                isLoading={isLoading}
            />

            <ProjectSettingsModal
                open={isSettingsModalOpen}
                onOpenChange={setIsSettingsModalOpen}
                project={project}
                onProjectUpdated={() => {
                    // Call the original onSettingsClick to refresh the data
                    onSettingsClick();
                }}
            />
        </div>
    );
}

export function ProjectVisibilityBadge({ isPublic }: { isPublic: boolean }) {
    return isPublic ? (
        <Badge
            variant="default"
            className="flex items-center gap-1 bg-green-900 text-white hover:bg-green-900"
        >
            <Share2Icon className="h-3 w-3" />
            Public
        </Badge>
    ) : (
        <Badge
            variant="default"
            className="flex items-center gap-1 bg-red-900 text-white hover:bg-red-900"
        >
            <LockIcon className="h-3 w-3" />
            Private
        </Badge>
    );
}
