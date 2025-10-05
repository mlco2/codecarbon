"use client";

import BreadcrumbHeader from "@/components/breadcrumb";
import ProjectDashboard from "@/components/project-dashboard";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import { getDefaultDateRange } from "@/helpers/date-utils";
import {
    getExperiments,
    getProjectEmissionsByExperiment,
} from "@/server-functions/experiments";
import { getOneProject } from "@/server-functions/projects";
import { Experiment } from "@/types/experiment";
import { ExperimentReport } from "@/types/experiment-report";
import { Project } from "@/types/project";
import { use, useCallback, useEffect, useState } from "react";
import { DateRange } from "react-day-picker";

export default function ProjectPage({
    params,
}: Readonly<{
    params: Promise<{
        projectId: string;
        organizationId: string;
    }>;
}>) {
    const { projectId, organizationId } = use(params);
    const [isLoading, setIsLoading] = useState(true);

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

    const [radialChartData, setRadialChartData] = useState({
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    });
    // The experiments of the current project. We need this because experimentReport only contains the experiments that have been run
    const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
        [],
    );
    // The reports (if any) of the experiments
    const [experimentsReportData, setExperimentsReportData] = useState<
        ExperimentReport[]
    >([]);

    const [runData, setRunData] = useState({
        experimentId: "",
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });

    const [convertedValues, setConvertedValues] = useState({
        citizen: "0",
        transportation: "0",
        tvTime: "0",
    });

    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    const refreshExperimentList = useCallback(async () => {
        // Logic to refresh experiments if needed
        const experiments: Experiment[] = await getExperiments(projectId);
        setProjectExperiments(experiments);
    }, [projectId]);

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

                const newRadialChartData = {
                    energy: {
                        label: "kWh",
                        value: parseFloat(
                            report
                                .reduce(
                                    (n, { energy_consumed }) =>
                                        n + energy_consumed,
                                    0,
                                )
                                .toFixed(2),
                        ),
                    },
                    emissions: {
                        label: "kg eq CO2",
                        value: parseFloat(
                            report
                                .reduce((n, { emissions }) => n + emissions, 0)
                                .toFixed(2),
                        ),
                    },
                    duration: {
                        label: "days",
                        value: parseFloat(
                            report
                                .reduce(
                                    (n, { duration }) => n + duration / 86400,
                                    0,
                                )
                                .toFixed(2),
                        ),
                    },
                };
                setRadialChartData(newRadialChartData);

                setExperimentsReportData(report);

                setRunData({
                    experimentId: report[0]?.experiment_id ?? "",
                    startDate: date?.from?.toISOString() ?? "",
                    endDate: date?.to?.toISOString() ?? "",
                });

                setSelectedExperimentId(report[0]?.experiment_id ?? "");

                setConvertedValues({
                    citizen: getEquivalentCitizenPercentage(
                        newRadialChartData.emissions.value,
                    ).toFixed(2),
                    transportation: getEquivalentCarKm(
                        newRadialChartData.emissions.value,
                    ).toFixed(2),
                    tvTime: getEquivalentTvTime(
                        newRadialChartData.energy.value,
                    ).toFixed(2),
                });
            } catch (error) {
                console.error("Error fetching project data:", error);
            } finally {
                setIsLoading(false);
            }
        }

        if (projectId) {
            fetchData();
        }
    }, [projectId, date]);

    const handleExperimentClick = useCallback(
        (experimentId: string) => {
            if (experimentId === selectedExperimentId) {
                setSelectedExperimentId("");
                setSelectedRunId("");
                return;
            }
            setSelectedExperimentId(experimentId);
            setSelectedRunId("");
        },
        [selectedExperimentId],
    );

    const handleRunClick = useCallback(
        (runId: string) => {
            if (runId === selectedRunId) {
                setSelectedRunId("");
                return;
            }
            setSelectedRunId(runId);
        },
        [selectedRunId],
    );

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
