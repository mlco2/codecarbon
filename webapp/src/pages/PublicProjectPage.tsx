import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { DateRange } from "react-day-picker";
import { ExperimentReport, Project, Experiment } from "@/api/schemas";
import PublicProjectDashboard from "@/components/public-project-dashboard";
import {
  getEquivalentCarKm,
  getEquivalentCitizenPercentage,
  getEquivalentTvTime,
} from "@/helpers/constants";
import { fetchApi } from "@/api/client";
import { ProjectSchema, ExperimentReportSchema, ExperimentSchema } from "@/api/schemas";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { getDefaultDateRange } from "@/helpers/date-utils";

export default function PublicProjectPage() {
  const { projectId: encryptedId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);

  const default_date = getDefaultDateRange();
  const [date, setDate] = useState<DateRange>(default_date);
  const [projectExperiments, setProjectExperiments] = useState<Experiment[]>([]);
  const [experimentsReportData, setExperimentsReportData] = useState<ExperimentReport[]>([]);

  const [radialChartData, setRadialChartData] = useState({
    energy: { label: "kWh", value: 0 },
    emissions: { label: "kg eq CO2", value: 0 },
    duration: { label: "days", value: 0 },
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
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string>("");

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

  // Decrypt the project ID via the backend
  useEffect(() => {
    const decrypt = async () => {
      try {
        setIsLoading(true);
        const result = await fetchApi(
          `/projects/public/${encryptedId}`,
          ProjectSchema,
        );
        setProjectId(result.id);
        setProject(result);
      } catch {
        setError("Invalid project link or the project no longer exists.");
      } finally {
        setIsLoading(false);
      }
    };
    decrypt();
  }, [encryptedId]);

  useEffect(() => {
    if (projectId && project) {
      refreshExperimentList();
    }
  }, [projectId, project, refreshExperimentList]);

  useEffect(() => {
    async function fetchData() {
      if (!projectId || !project) return;

      setIsLoading(true);
      try {
        const report = await fetchApi(
          `/projects/${projectId}/experiments/sums?start_date=${date?.from?.toISOString()}&end_date=${date?.to?.toISOString()}`,
          ExperimentReportSchema.array(),
        );

        setExperimentsReportData(report);

        const newRadialChartData = {
          energy: {
            label: "kWh",
            value: parseFloat(
              report.reduce((n, { energy_consumed }) => n + energy_consumed, 0).toFixed(2),
            ),
          },
          emissions: {
            label: "kg eq CO2",
            value: parseFloat(
              report.reduce((n, { emissions }) => n + emissions, 0).toFixed(2),
            ),
          },
          duration: {
            label: "days",
            value: parseFloat(
              report.reduce((n, { duration }) => n + duration / 86400, 0).toFixed(2),
            ),
          },
        };

        setRadialChartData(newRadialChartData);

        if (report.length > 0) {
          setRunData({
            experimentId: report[0]?.experiment_id ?? "",
            startDate: date?.from?.toISOString() ?? "",
            endDate: date?.to?.toISOString() ?? "",
          });
          setSelectedExperimentId(report[0]?.experiment_id ?? "");
        }

        setConvertedValues({
          citizen: getEquivalentCitizenPercentage(newRadialChartData.emissions.value).toFixed(2),
          transportation: getEquivalentCarKm(newRadialChartData.emissions.value).toFixed(2),
          tvTime: getEquivalentTvTime(newRadialChartData.energy.value).toFixed(2),
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
    setRunData((prevData) => ({ ...prevData, experimentId }));
    setSelectedRunId("");
  }, []);

  const handleRunClick = useCallback((runId: string) => {
    setSelectedRunId(runId);
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
          onDateChange={(newDates) => setDate(newDates || getDefaultDateRange())}
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
