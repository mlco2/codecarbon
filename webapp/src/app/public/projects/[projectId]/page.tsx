"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { DateRange } from "react-day-picker";
import { decryptProjectId } from "@/utils/crypto";
import { ExperimentReport } from "@/types/experiment-report";
import PublicProjectDashboard from "@/components/public-project-dashboard";
import { fetchApi } from "@/utils/api";
import { Project } from "@/types/project";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { useProjectDashboard } from "@/hooks/useProjectDashboard";

export default function PublicProjectPage({
    params,
}: {
    params: Promise<{ projectId: string }>;
}) {
    const { projectId: encryptedId } = use(params);
    const router = useRouter();

    const [error, setError] = useState<string | null>(null);
    const [projectId, setProjectId] = useState<string | null>(null);
    const [project, setProject] = useState<Project | null>(null);

    // Dashboard state
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
    }, [encryptedId, setIsLoading]);

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

        if (projectId && !project) {
            fetchProjectData();
            refreshExperimentList();
        }
    }, [projectId, project, refreshExperimentList, setIsLoading]);

    // Fetch experiments and emissions data
    useEffect(() => {
        async function fetchData() {
            if (!projectId || !project) return;

            setIsLoading(true);
            try {
                const report = await fetchApi<ExperimentReport[]>(
                    `/projects/${projectId}/experiments/sums?start_date=${date?.from?.toISOString()}&end_date=${date?.to?.toISOString()}`,
                );

                if (!report) {
                    return;
                }

                setExperimentsReportData(report);
            } catch (error) {
                console.error("Error fetching data:", error);
            } finally {
                setIsLoading(false);
            }
        }

        if (projectId && project) {
            fetchData();
        }
    }, [projectId, project, date, setExperimentsReportData, setIsLoading]);

    // Show full page loader only during initial load
    if (isLoading && !project) {
        return <Loader />;
    }

    if (error) {
        return (
            <div className="container mx-auto p-8 h-screen flex flex-col justify-center items-center">
                <Alert variant="default" className="w-[500px]">
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
                    projectExperiments={projectExperiments}
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
