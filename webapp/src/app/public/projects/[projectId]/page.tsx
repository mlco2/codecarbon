"use client";

import { useState, useEffect, useCallback, use } from "react";
import { DateRange } from "react-day-picker";
import { useRouter } from "next/navigation";
import { getOneProject } from "@/server-functions/projects";
import { Project } from "@/types/project";
import { getProjectEmissionsByExperiment } from "@/server-functions/experiments";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import ProjectDashboard from "@/components/public-project-dashboard";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { fiefAuth } from "@/helpers/fief";

export default function PublicProjectPage({
    params,
}: Readonly<{
    params: Promise<{
        projectId: string;
    }>;
}>) {
    const { projectId } = use(params);
    const router = useRouter();
    const tokenInfo = fiefAuth.getAccessTokenInfo();
    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);

    useEffect(() => {
        const fetchProjectDetails = async () => {
            try {
                const project: Project = await getOneProject(projectId);
                if (!project.public) {
                    // Redirect to home if project is not public
                    router.push("/");
                    return;
                }
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
                router.push("/");
            }
        };

        fetchProjectDetails();
    }, [projectId, router]);

    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);
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
            try {
                const report = await getProjectEmissionsByExperiment(
                    tokenInfo?.access_token ?? null,
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
            } catch (error) {
                console.error("Error fetching project data:", error);
            }
        }

        if (project.id) {
            fetchData();
        }
    }, [projectId, date, project.id, tokenInfo?.access_token]);

    const handleExperimentClick = useCallback((experimentId: string) => {
        setSelectedExperimentId(experimentId);
        setRunData((prevData) => ({
            ...prevData,
            experimentId: experimentId,
        }));
        setSelectedRunId(""); // Reset selected runId
    }, []);

    const handleRunClick = useCallback((runId: string) => {
        setSelectedRunId(runId);
    }, []);

    return (
        <div className="container mx-auto px-4 py-8">
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
            />
        </div>
    );
}
