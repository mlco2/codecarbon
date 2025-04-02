"use client";

import BreadcrumbHeader from "@/components/breadcrumb";
import ProjectDashboard from "@/components/project-dashboard";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import { getProjectEmissionsByExperiment } from "@/server-functions/experiments";
import { getOneProject } from "@/server-functions/projects";
import { ExperimentReport } from "@/types/experiment-report";
import { Project } from "@/types/project";
import { addMonths, endOfDay, startOfDay } from "date-fns";
import { useRouter } from "next/navigation";
import { use, useCallback, useEffect, useState } from "react";
import { DateRange } from "react-day-picker";

// Fonction pour obtenir la plage de dates par défaut
const getDefaultDateRange = (): { from: Date; to: Date } => {
    const today = new Date();
    return {
        from: startOfDay(addMonths(today, -2)),
        to: endOfDay(today),
    };
};

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

    useEffect(() => {
        // Replace with your actual API endpoint
        const fetchProjectDetails = async () => {
            try {
                const project: Project = await getOneProject(projectId);
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
            }
        };

        fetchProjectDetails();
    }, [projectId]);
    const router = useRouter();
    const handleSettingsClick = () => {
        router.push(`/${organizationId}/projects/${projectId}/settings`);
    };

    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);
    const [experimentReport, setExperimentReport] = useState<
        ExperimentReport[]
    >([]);
    const [radialChartData, setRadialChartData] = useState({
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    });
    const [experimentsData, setExperimentsData] = useState({
        projectId: projectId,
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });
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

    useEffect(() => {
        async function fetchData() {
            const report = await getProjectEmissionsByExperiment(
                projectId,
                date,
            );
            setExperimentReport(report);

            const newRadialChartData = {
                energy: {
                    label: "kWh",
                    value: parseFloat(
                        report
                            .reduce(
                                (n, { energy_consumed }) => n + energy_consumed,
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

            setExperimentsData({
                projectId: projectId,
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

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
        }

        fetchData();
    }, [projectId, date]);

    const handleExperimentClick = useCallback((experimentId: string) => {
        setSelectedExperimentId(experimentId);
        setRunData((prevData) => ({
            ...prevData,
            experimentId: experimentId,
        }));
        setSelectedRunId(""); // Réinitialiser le runId sélectionné
    }, []);

    const handleRunClick = useCallback((runId: string) => {
        setSelectedRunId(runId);
    }, []);

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
                    experimentsData={experimentsData}
                    runData={runData}
                    selectedExperimentId={selectedExperimentId}
                    selectedRunId={selectedRunId}
                    onExperimentClick={handleExperimentClick}
                    onRunClick={handleRunClick}
                    onSettingsClick={handleSettingsClick}
                    organizationId={organizationId}
                />
            </div>
        </div>
    );
}
