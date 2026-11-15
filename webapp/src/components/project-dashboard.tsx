import { ProjectDashboardProps } from "@/api/schemas";
import ProjectDashboardBase from "./project-dashboard-base";

/*
 * The private project dashboard: the shared panels, wired to the authenticated
 * data.
 *
 * The project's own controls — refresh, share, export, settings — used to live
 * here as a header row passed down to the base. They now sit in the page's
 * heading beside the project's name, as `ProjectActions`, so nothing about the
 * project's identity is rendered from inside its panels.
 */
export default function ProjectDashboard({
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
    onRefresh,
    isLoading,
}: ProjectDashboardProps) {
    return (
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
            onExperimentCreated={onRefresh}
            projectExperiments={projectExperiments}
            isLoading={isLoading}
        />
    );
}
