import { PublicProjectDashboardProps } from "@/types/public-project-dashboard";
import ProjectDashboardBase from "./project-dashboard-base";
import { Badge } from "@/components/ui/badge";
import { Share2Icon } from "lucide-react";

export default function PublicProjectDashboard({
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
    isLoading,
}: PublicProjectDashboardProps) {
    const headerContent = (
        <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold">{project.name}</h1>
                <Badge variant="secondary" className="flex items-center gap-1">
                    <Share2Icon className="h-3 w-3" />
                    Public
                </Badge>
            </div>
            <p className="text-muted-foreground">{project.description}</p>
        </div>
    );

    return (
        <ProjectDashboardBase
            isPublicView={true}
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
    );
}
