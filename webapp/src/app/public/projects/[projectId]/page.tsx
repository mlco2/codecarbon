"use client";

import { useState, useEffect, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import { DateRange } from "react-day-picker";
import { decryptProjectId } from "@/utils/crypto";
import { ExperimentReport } from "@/types/experiment-report";
import PublicProjectDashboard from "@/components/public-project-dashboard";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import { fetchApi } from "@/utils/api";
import { Project } from "@/types/project";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { getDefaultDateRange } from "@/helpers/date-utils";

export default function PublicProjectPage({
    params,
}: {
    params: Promise<{ projectId: string }>;
}) {
    const { projectId: encryptedId } = use(params);
    const router = useRouter();

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [projectId, setProjectId] = useState<string | null>(null);
    const [project, setProject] = useState<Project | null>(null);

    // Dashboard state
    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);
    const [experimentsReportData, setExperimentsReportData] = useState<
        ExperimentReport[]
    >([]);
    const [radialChartData, setRadialChartData] = useState({
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    });
    const [experimentsData, setExperimentsData] = useState({
        projectId: "",
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

    // Decrypt the project ID
    useEffect(() => {
        const decrypt = async () => {
            try {
                setIsLoading(true);
                const decryptedId = await decryptProjectId(encryptedId);
                setProjectId(decryptedId);
            } catch (error) {
                console.error("Failed to decrypt project ID:", error);
                setError(
                    "Invalid project link or the project no longer exists.",
                );
            }
        };

        decrypt();
    }, [encryptedId]);

    // Fetch project data
    useEffect(() => {
        const fetchProjectData = async () => {
            if (!projectId) return;

            try {
                // Use regular endpoint - the backend already handles public projects without auth
                const projectData = await fetchApi<Project>(
                    `/projects/${projectId}`,
                );

                if (!projectData || !projectData.public) {
                    setError(
                        "This project is not available for public viewing.",
                    );
                    return;
                }

                setProject(projectData);
            } catch (error) {
                console.error("Error fetching project:", error);
                setError("Failed to load project data.");
            } finally {
                setIsLoading(false);
            }
        };

        if (projectId) {
            fetchProjectData();
        }
    }, [projectId]);

    // Fetch experiments and emissions data
    useEffect(() => {
        async function fetchData() {
            if (!projectId) return;

            setIsLoading(true);
            try {
                const report = await fetchApi<ExperimentReport[]>(
                    `/projects/${projectId}/experiments/sums?start_date=${date?.from?.toISOString()}&end_date=${date?.to?.toISOString()}`,
                );

                if (!report) {
                    return;
                }

                setExperimentsReportData(report);

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

                if (report.length > 0) {
                    setRunData({
                        experimentId: report[0]?.experiment_id ?? "",
                        startDate: date?.from?.toISOString() ?? "",
                        endDate: date?.to?.toISOString() ?? "",
                    });

                    setSelectedExperimentId(report[0]?.experiment_id ?? "");
                }

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
                console.error("Error fetching data:", error);
            } finally {
                setIsLoading(false);
            }
        }

        if (projectId && project) {
            fetchData();
        }
    }, [projectId, project, date]);

    const handleExperimentClick = useCallback((experimentId: string) => {
        setSelectedExperimentId(experimentId);
        setRunData((prevData) => ({
            ...prevData,
            experimentId: experimentId,
        }));
        setSelectedRunId(""); // Reset the run ID
    }, []);

    const handleRunClick = useCallback((runId: string) => {
        setSelectedRunId(runId);
    }, []);

    // Show full page loader only during initial load
    if (isLoading && !project) {
        return <Loader />;
    }

    if (error) {
        return (
            <div className="container mx-auto p-8">
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
                <div className="mt-4 flex justify-center">
                    <button
                        onClick={() => router.push("/")}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
                    >
                        Go to Homepage
                    </button>
                </div>
            </div>
        );
    }

    if (!project) {
        return <ErrorMessage />;
    }

    return (
        <div className="container mx-auto p-8">
            <div className="flex flex-col gap-4">
                <PublicProjectDashboard
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
                    onExperimentClick={handleExperimentClick}
                    onRunClick={handleRunClick}
                    isLoading={isLoading}
                />
            </div>
        </div>
    );
}
