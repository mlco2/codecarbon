import BreadcrumbHeader from "@/components/breadcrumb";
import ProjectDashboard from "@/components/project-dashboard";
import {
    calculateConvertedValues,
    calculateRadialChartData,
    getDefaultConvertedValues,
    getDefaultRadialChartData,
} from "@/helpers/dashboard-calculations";
import { getDefaultDateRange } from "@/helpers/date-utils";
import {
    getExperiments,
    getProjectEmissionsByExperiment,
} from "@/api/experiments";
import { getOneProject } from "@/api/projects";
import { Experiment, ExperimentReport, Project } from "@/api/schemas";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { DateRange } from "react-day-picker";

export default function ProjectDashboardPage() {
    const { projectId, organizationId } = useParams<{
        projectId: string;
        organizationId: string;
    }>();

    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);
    const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
        [],
    );
    const [experimentsReportData, setExperimentsReportData] = useState<
        ExperimentReport[]
    >([]);
    const [isLoading, setIsLoading] = useState(true);

    const [date, setDate] = useState<DateRange>(() => getDefaultDateRange());
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

    const loadProjectAndExperiments = useCallback(async () => {
        if (!projectId) return;
        const [p, experiments] = await Promise.all([
            getOneProject(projectId),
            getExperiments(projectId),
        ]);
        if (p) setProject(p);
        setProjectExperiments(experiments);
    }, [projectId]);

    const loadReport = useCallback(
        async (dateRange: DateRange) => {
            if (!projectId) return;
            setIsLoading(true);
            try {
                const report = await getProjectEmissionsByExperiment(
                    projectId,
                    dateRange,
                );
                setExperimentsReportData(report);
            } finally {
                setIsLoading(false);
            }
        },
        [projectId],
    );

    useEffect(() => {
        loadProjectAndExperiments();
    }, [loadProjectAndExperiments]);

    useEffect(() => {
        loadReport(date);
    }, [loadReport, date]);

    const handleRefresh = useCallback(() => {
        loadProjectAndExperiments();
        loadReport(date);
    }, [loadProjectAndExperiments, loadReport, date]);

    const handleSettingsClick = async () => {
        if (!projectId) return;
        const updatedProject = await getOneProject(projectId);
        if (updatedProject) setProject(updatedProject);
    };

    const handleExperimentClick = useCallback(
        (experimentId: string) => {
            setSelectedExperimentId(
                experimentId === selectedExperimentId ? "" : experimentId,
            );
            setSelectedRunId("");
        },
        [selectedExperimentId],
    );

    const handleRunClick = useCallback(
        (runId: string) => {
            setSelectedRunId(runId === selectedRunId ? "" : runId);
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
                            organizationId!,
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
