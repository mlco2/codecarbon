import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { DateRange } from "react-day-picker";
import { ExperimentReport, Project, Experiment } from "@/api/schemas";
import PublicProjectDashboard from "@/components/public-project-dashboard";
import {
    calculateConvertedValues,
    calculateRadialChartData,
    getDefaultConvertedValues,
    getDefaultRadialChartData,
} from "@/helpers/dashboard-calculations";
import { fetchApi } from "@/api/client";
import { getProjectEmissionsByExperiment } from "@/api/experiments";
import { ProjectSchema, ExperimentSchema } from "@/api/schemas";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { decryptProjectId } from "@/utils/crypto";

export default function PublicProjectPage() {
    const { projectId: encryptedId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [projectId, setProjectId] = useState<string | null>(null);
    const [project, setProject] = useState<Project | null>(null);

    const [date, setDate] = useState<DateRange>(() => getDefaultDateRange());
    const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
        [],
    );
    const [experimentsReportData, setExperimentsReportData] = useState<
        ExperimentReport[]
    >([]);

    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    const radialChartData = useMemo(
        () =>
            experimentsReportData.length > 0
                ? calculateRadialChartData(experimentsReportData)
                : getDefaultRadialChartData(),
        [experimentsReportData],
    );
    const convertedValues = useMemo(
        () =>
            experimentsReportData.length > 0
                ? calculateConvertedValues(radialChartData)
                : getDefaultConvertedValues(),
        [experimentsReportData.length, radialChartData],
    );
    const runData = useMemo(
        () => ({
            experimentId: selectedExperimentId,
            startDate: date.from?.toISOString() ?? "",
            endDate: date.to?.toISOString() ?? "",
        }),
        [date, selectedExperimentId],
    );

    const refreshExperimentList = useCallback(async () => {
        if (!projectId) return;
        try {
            const experiments = await fetchApi(
                `/projects/${projectId}/experiments`,
                ExperimentSchema.array(),
            );
            setProjectExperiments(experiments);
        } catch {
            setProjectExperiments([]);
        }
    }, [projectId]);

    // Decrypt the project ID client-side. The encrypted token is computed
    // with the same key in `ShareProjectButton`, so decryption is purely
    // local — no backend round-trip required.
    useEffect(() => {
        const decrypt = async () => {
            if (!encryptedId) return;
            try {
                const decryptedId = await decryptProjectId(encryptedId);
                setProjectId(decryptedId);
            } catch (err) {
                console.error("Failed to decrypt project ID:", err);
                setError(
                    "Invalid project link or the project no longer exists.",
                );
                setIsLoading(false);
            }
        };
        decrypt();
    }, [encryptedId]);

    // Once we have the real project id, fetch the project. The backend
    // already serves public projects through the regular endpoint without
    // authentication.
    useEffect(() => {
        const fetchProjectData = async () => {
            if (!projectId || project) return;
            try {
                setIsLoading(true);
                const projectData = await fetchApi(
                    `/projects/${projectId}`,
                    ProjectSchema,
                );
                if (!projectData.public) {
                    setError(
                        "This project is not available for public viewing.",
                    );
                    return;
                }
                setProject(projectData);
            } catch (err) {
                console.error("Error fetching project:", err);
                setError("Failed to load project data.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchProjectData();
    }, [projectId, project]);

    useEffect(() => {
        if (projectId && project) {
            refreshExperimentList();
        }
    }, [projectId, project, refreshExperimentList]);

    useEffect(() => {
        if (!projectId || !project) return;
        let cancelled = false;
        (async () => {
            setIsLoading(true);
            try {
                const report = await getProjectEmissionsByExperiment(
                    projectId,
                    date,
                );
                if (!cancelled) setExperimentsReportData(report);
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [projectId, project, date]);

    const handleExperimentClick = useCallback(
        (experimentId: string) => {
            setSelectedExperimentId((current) =>
                experimentId === current ? "" : experimentId,
            );
            setSelectedRunId("");
        },
        [],
    );

    const handleRunClick = useCallback((runId: string) => {
        setSelectedRunId((current) => (runId === current ? "" : runId));
    }, []);

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
                        onClick={() => navigate("/")}
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
                    onDateChange={(newDates) =>
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
