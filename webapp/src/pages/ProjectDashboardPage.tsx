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
} from "@/api/experiments";
import { getOneProject } from "@/api/projects";
import { Experiment, ExperimentReport, Project } from "@/api/schemas";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { DateRange } from "react-day-picker";

export default function ProjectDashboardPage() {
  const { projectId, organizationId } = useParams<{
    projectId: string;
    organizationId: string;
  }>();
  const [isLoading, setIsLoading] = useState(true);

  const [project, setProject] = useState({
    name: "",
    description: "",
  } as Project);

  const default_date = getDefaultDateRange();
  const [date, setDate] = useState<DateRange>(default_date);

  const [radialChartData, setRadialChartData] = useState({
    energy: { label: "kWh", value: 0 },
    emissions: { label: "kg eq CO2", value: 0 },
    duration: { label: "days", value: 0 },
  });
  const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
    [],
  );
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
    const experiments: Experiment[] = await getExperiments(projectId!);
    setProjectExperiments(experiments);
  }, [projectId]);

  const fetchEmissionsReport = useCallback(
    async (dateRange: DateRange) => {
      setIsLoading(true);
      try {
        const report = await getProjectEmissionsByExperiment(
          projectId!,
          dateRange,
        );

        const newRadialChartData = {
          energy: {
            label: "kWh",
            value: parseFloat(
              report
                .reduce((n, { energy_consumed }) => n + energy_consumed, 0)
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
                .reduce((n, { duration }) => n + duration / 86400, 0)
                .toFixed(2),
            ),
          },
        };
        setRadialChartData(newRadialChartData);
        setExperimentsReportData(report);
        setRunData({
          experimentId: report[0]?.experiment_id ?? "",
          startDate: dateRange?.from?.toISOString() ?? "",
          endDate: dateRange?.to?.toISOString() ?? "",
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
    },
    [projectId],
  );

  const handleSettingsClick = async () => {
    try {
      const updatedProject = await getOneProject(projectId!);
      if (updatedProject) {
        setProject(updatedProject);
      }
    } catch (error) {
      console.error("Error refreshing project data:", error);
    }
  };

  const handleRefresh = useCallback(async () => {
    const projectPromise = getOneProject(projectId!).then((p) => {
      if (p) setProject(p);
    });
    const experimentsPromise = refreshExperimentList();
    const reportPromise = fetchEmissionsReport(date);
    await Promise.all([projectPromise, experimentsPromise, reportPromise]);
  }, [projectId, date, refreshExperimentList, fetchEmissionsReport]);

  useEffect(() => {
    const fetchProjectDetails = async () => {
      try {
        const p = await getOneProject(projectId!);
        if (!p) return;
        setProject(p);
      } catch (error) {
        console.error("Error fetching project description:", error);
      }
    };

    fetchProjectDetails();
    refreshExperimentList();
  }, [projectId, refreshExperimentList]);

  useEffect(() => {
    if (projectId) {
      fetchEmissionsReport(date);
    }
  }, [projectId, date, fetchEmissionsReport]);

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
              localStorage.getItem("organizationName") || organizationId!,
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
          onDateChange={(newDates) =>
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
          onRefresh={handleRefresh}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
