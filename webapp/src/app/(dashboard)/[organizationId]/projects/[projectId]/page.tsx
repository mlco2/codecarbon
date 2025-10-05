"use client";

import BreadcrumbHeader from "@/components/breadcrumb";
import ProjectDashboard from "@/components/project-dashboard";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { getProjectEmissionsByExperiment } from "@/server-functions/experiments";
import { getOneProject } from "@/server-functions/projects";
import { Project } from "@/types/project";
import { use, useEffect, useState } from "react";
import { DateRange } from "react-day-picker";
import { useProjectDashboard } from "@/hooks/useProjectDashboard";

export default function ProjectPage({
    params,
}: Readonly<{
    params: Promise<{
        projectId: string;
        organizationId: string;
    }>;
}>) {
    const { projectId, organizationId } = use(params);

    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);

    // This function now just refreshes the project data instead of navigating
    const handleSettingsClick = async () => {
        try {
            const updatedProject = await getOneProject(projectId);
            if (updatedProject) {
                setProject(updatedProject);
            }
        } catch (error) {
            console.error("Error refreshing project data:", error);
        }
    };

    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);

    // Use custom hook for dashboard state and logic
    const {
        radialChartData,
        convertedValues,
        experimentsReportData,
        projectExperiments,
        runData,
        selectedExperimentId,
        selectedRunId,
        isLoading,
        handleExperimentClick,
        handleRunClick,
        refreshExperimentList,
        setExperimentsReportData,
        setIsLoading,
    } = useProjectDashboard(projectId, date);

    /** Use effect functions */
    useEffect(() => {
        const fetchProjectDetails = async () => {
            try {
                const project: Project | null = await getOneProject(projectId);
                if (!project) {
                    return;
                }
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
            }
        };

        fetchProjectDetails();
        refreshExperimentList();
    }, [projectId, refreshExperimentList]);

    // Fetch the experiment report of the current project
    useEffect(() => {
        async function fetchData() {
            setIsLoading(true);
            try {
                const report = await getProjectEmissionsByExperiment(
                    projectId,
                    date,
                );
                setExperimentsReportData(report);
            } catch (error) {
                console.error("Error fetching project data:", error);
            } finally {
                setIsLoading(false);
            }
        }

        if (projectId) {
            fetchData();
        }
    }, [projectId, date, setExperimentsReportData, setIsLoading]);

    return (
        <div className="h-full w-full overflow-auto">
            <BreadcrumbHeader
                pathSegments={[
                    {
                        title:
                            localStorage.getItem("organizationName") ||
                            organizationId,
                        href: `/${organizationId}`,
                    },
                    {
                        title: "Projects",
                        href: `/${organizationId}/projects`,
                    },
                    {
                        title: `Project ${project.name || ""}`,
                        href: null,
                    },
                ]}
            />
            <div className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                <ProjectDashboard
                    project={project}
                    date={date}
                    onDateChange={(newDates: DateRange | undefined) =>
                        setDate(newDates || getDefaultDateRange())
                    }
                    radialChartData={radialChartData}
                    convertedValues={convertedValues}
                    experimentsReportData={experimentsReportData}
                    runData={runData}
                    selectedExperimentId={selectedExperimentId}
                    selectedRunId={selectedRunId}
                    projectExperiments={projectExperiments}
                    onExperimentClick={handleExperimentClick}
                    onRunClick={handleRunClick}
                    onSettingsClick={handleSettingsClick}
                    isLoading={isLoading}
                />
            </div>
        </div>
    );
}
