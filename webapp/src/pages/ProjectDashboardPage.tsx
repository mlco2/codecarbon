import ProjectActions from "@/components/project-actions";
import ProjectDashboard from "@/components/project-dashboard";
import ProjectVisibilityBadge from "@/components/project-visibility-badge";
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
import { Link, useParams } from "react-router-dom";
import { DateRange } from "react-day-picker";

export default function ProjectDashboardPage() {
    const { projectId, organizationId } = useParams<{
        projectId: string;
        organizationId: string;
    }>();
    let organizationName: string | null = null;
    try {
        organizationName = localStorage.getItem("organizationName");
    } catch {
        organizationName = null;
    }

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
        /*
         * The redesign's content column, as the Global dashboard and the Projects
         * page use it: one scrolling region whose padding is the single horizontal
         * gutter for everything inside.
         *
         * Only the shell is redesigned so far — the surface, the breadcrumb and
         * the page heading. The panels below are still the old dashboard.
         */
        <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-cc-page-background px-5 pb-10 pt-4 sm:px-10 lg:px-20 lg:pb-8 lg:pt-5">
            {/* Parent crumbs hover to white: the current crumb is the green one,
                so hovering a link must not make it look like the page you are
                already on. */}
            <nav
                aria-label="Breadcrumb"
                className="type-mono-medium type-breadcrumb pb-8 lg:pb-16"
            >
                <Link
                    to={`/${organizationId}`}
                    className="text-cc-breadcrumb-gray transition-colors hover:text-cc-white motion-reduce:transition-none"
                >
                    {organizationName || organizationId}/
                </Link>
                <Link
                    to={`/${organizationId}/projects`}
                    className="text-cc-breadcrumb-gray transition-colors hover:text-cc-white motion-reduce:transition-none"
                >
                    Projects/
                </Link>
                <span className="text-cc-button-hover">{project.name}</span>
            </nav>

            {/* The heading holds everything about the project itself: its name,
                whether it is public, what it is, and the actions that apply to
                it. The actions sit at the end of the row and drop below the
                name when there is no room for both. */}
            <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-4 border-b border-cc-rule pb-5 lg:pb-6">
                <div className="flex min-w-0 flex-col gap-2">
                    {/* The visibility pill belongs with the name it describes,
                        so it sits on the title's line and wraps under it when
                        there is no room. */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                        <h1 className="type-display type-page-title min-w-0 text-cc-white">
                            {project.name}
                        </h1>
                        {project.public !== undefined && (
                            <ProjectVisibilityBadge isPublic={project.public} />
                        )}
                    </div>
                    {project.description && (
                        <p className="type-mono-medium type-page-subtitle text-cc-white">
                            {project.description}
                        </p>
                    )}
                </div>

                <ProjectActions
                    project={project}
                    experimentsReportData={experimentsReportData}
                    runData={runData}
                    onRefresh={handleRefresh}
                    onProjectUpdated={handleSettingsClick}
                    className="shrink-0"
                />
            </header>

            <div className="flex flex-col gap-4 pt-6 md:gap-8 lg:pt-8">
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
                    onRefresh={handleRefresh}
                    isLoading={isLoading}
                />
            </div>
        </div>
    );
}
