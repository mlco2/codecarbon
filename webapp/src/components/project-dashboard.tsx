import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SettingsIcon, Share2Icon, LockIcon } from "lucide-react";
import { ProjectDashboardProps } from "@/types/project-dashboard";
import ProjectDashboardBase from "./project-dashboard-base";
import ShareProjectButton from "./share-project-button";
import ProjectSettingsModal from "./project-settings-modal";
import { useState } from "react";

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
