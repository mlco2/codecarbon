import { useState } from "react";
import { toast } from "sonner";

import {
    getEmissionsTimeSeries,
    getRunEmissionsByExperiment,
} from "@/api/runs";
import { ExperimentReport, Project } from "@/api/schemas";
import { useModal } from "@/hooks/useModal";
import { cn } from "@/helpers/utils";
import { exportToJson } from "@/utils/export";
import ProjectSettingsModal from "./project-settings-modal";
import { DownloadIcon } from "./icons/download-icon";
import { RefreshIcon } from "./icons/refresh-icon";
import { SettingsIcon } from "./icons/settings-icon";
import ShareProjectButton from "./share-project-button";
import { IconButton } from "./ui/icon-button";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "./ui/tooltip";

/*
 * The actions that apply to a project as a whole: refresh, share, export, and
 * settings.
 *
 * Its own component so it can sit in the page's heading, beside the project's
 * name, rather than inside the panels below — the dashboard's data flows down,
 * but these controls belong to the project, not to any panel. It owns the state
 * only it uses (the refresh and export spinners, the settings dialog).
 *
 * The controls are square outlined icon buttons, so they carry the same radius
 * and the same hover as every other control in the app.
 */
export default function ProjectActions({
    project,
    experimentsReportData,
    runData,
    onRefresh,
    onProjectUpdated,
    className,
}: Readonly<{
    project: Project;
    experimentsReportData: ExperimentReport[];
    runData: { experimentId: string; startDate: string; endDate: string };
    /** Refetches the dashboard, behind the refresh control. */
    onRefresh: () => void | Promise<void>;
    /** Runs after the settings dialog saves; defaults to a full refresh. */
    onProjectUpdated?: () => void | Promise<void>;
    className?: string;
}>) {
    const settingsModal = useModal();
    const [isExporting, setIsExporting] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await onRefresh();
        } finally {
            setIsRefreshing(false);
        }
    };

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

    return (
        <div className={className}>
            <div className="flex flex-wrap items-center gap-2">
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <IconButton
                                aria-label="Refresh data"
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                            >
                                <RefreshIcon
                                    className={cn(
                                        "size-6",
                                        isRefreshing &&
                                            "animate-spin motion-reduce:animate-none",
                                    )}
                                />
                            </IconButton>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Refresh data</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <ShareProjectButton
                    projectId={project.id}
                    isPublic={project.public}
                />
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <IconButton
                                aria-label="Download JSON export"
                                onClick={handleJsonExport}
                                disabled={isExporting}
                            >
                                <DownloadIcon
                                    className={cn(
                                        "size-6",
                                        isExporting &&
                                            "animate-pulse motion-reduce:animate-none",
                                    )}
                                />
                            </IconButton>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Download JSON export</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <IconButton
                    aria-label="Project settings"
                    onClick={settingsModal.open}
                >
                    <SettingsIcon className="size-6" />
                </IconButton>
            </div>

            <ProjectSettingsModal
                open={settingsModal.isOpen}
                onOpenChange={settingsModal.setIsOpen}
                project={project}
                onProjectUpdated={onProjectUpdated ?? onRefresh}
            />
        </div>
    );
}
