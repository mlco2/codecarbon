"use client";

import BreadcrumbHeader from "@/components/breadcrumb";
import ProjectDashboard from "@/components/project-dashboard";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { fetcher } from "@/helpers/swr";
import { REFRESH_INTERVAL_ONE_MINUTE } from "@/helpers/time-constants";
import { Experiment } from "@/types/experiment";
import { ExperimentReport } from "@/types/experiment-report";
import { Project } from "@/types/project";
import { use, useCallback, useEffect, useMemo, useState } from "react";
import { DateRange } from "react-day-picker";
import useSWR, { mutate } from "swr";

export default function ProjectPage({
    params,
}: Readonly<{
    params: Promise<{
        projectId: string;
        organizationId: string;
    }>;
}>) {
    const { projectId, organizationId } = use(params);

    const default_date = useMemo(() => getDefaultDateRange(), []);
    const [date, setDate] = useState<DateRange>(default_date);

    // Fetch project details
    const { data: project } = useSWR<Project>(
        `/projects/${projectId}`,
        fetcher,
        {
            refreshInterval: REFRESH_INTERVAL_ONE_MINUTE,
        },
    );

    // Fetch experiments list
    const { data: projectExperiments = [] } = useSWR<Experiment[]>(
        `/projects/${projectId}/experiments`,
        fetcher,
        {
            refreshInterval: REFRESH_INTERVAL_ONE_MINUTE,
        },
    );

    // Construct report URL with date filters
    const reportUrl = useMemo(() => {
        let url = `/projects/${projectId}/experiments/sums`;
        if (date?.from || date?.to) {
            const params = new URLSearchParams();
            if (date.from) {
                params.append("start_date", date.from.toISOString());
            }
            if (date.to) {
                params.append("end_date", date.to.toISOString());
            }
            url += `?${params.toString()}`;
        }
        return url;
    }, [projectId, date]);

    // Fetch emissions report
    const {
        data: experimentsReportData = [],
        isLoading,
        error,
    } = useSWR<ExperimentReport[]>(reportUrl, fetcher, {
        refreshInterval: REFRESH_INTERVAL_ONE_MINUTE,
    });

    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    // Initialize selectedExperimentId when data arrives
    useEffect(() => {
        if (!selectedExperimentId && experimentsReportData.length > 0) {
            setSelectedExperimentId(experimentsReportData[0].experiment_id);
        }
    }, [experimentsReportData, selectedExperimentId]);

    // Derive radial chart data
    const radialChartData = useMemo(() => {
        return {
            energy: {
                label: "kWh",
                value: parseFloat(
                    experimentsReportData
                        .reduce(
                            (n, { energy_consumed }) => n + (energy_consumed ?? 0),
                            0,
                        )
                        .toFixed(2),
                ),
            },
            emissions: {
                label: "kg eq CO2",
                value: parseFloat(
                    experimentsReportData
                        .reduce((n, { emissions }) => n + (emissions ?? 0), 0)
                        .toFixed(2),
                ),
            },
            duration: {
                label: "days",
                value: parseFloat(
                    experimentsReportData
                        .reduce((n, { duration }) => n + (duration ?? 0) / 86400, 0)
                        .toFixed(2),
                ),
            },
        };
    }, [experimentsReportData]);

    // Derive converted values
    const convertedValues = useMemo(() => {
        return {
            citizen: getEquivalentCitizenPercentage(
                radialChartData.emissions.value,
            ).toFixed(2),
            transportation: getEquivalentCarKm(
                radialChartData.emissions.value,
            ).toFixed(2),
            tvTime: getEquivalentTvTime(radialChartData.energy.value).toFixed(
                2,
            ),
        };
    }, [radialChartData]);

    // Derive run data
    const runData = useMemo(() => {
        return {
            experimentId: selectedExperimentId || experimentsReportData[0]?.experiment_id || "",
            startDate: date?.from?.toISOString() ?? "",
            endDate: date?.to?.toISOString() ?? "",
        };
    }, [selectedExperimentId, experimentsReportData, date]);

    const handleSettingsClick = async () => {
        mutate(`/projects/${projectId}`);
    };

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

    if (error) {
        console.error("Error fetching project data:", error);
        return (
            <div className="flex h-full w-full items-center justify-center p-8">
                <div className="text-center">
                    <h2 className="text-lg font-semibold text-red-600">Failed to load data</h2>
                    <p className="text-sm text-gray-500">Please try refreshing the page or check your connection.</p>
                </div>
            </div>
        );
    }

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
                        title: `Project ${project?.name || ""}`,
                        href: null,
                    },
                ]}
            />
            <div className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                <ProjectDashboard
                    project={project || ({ name: "", description: "" } as Project)}
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

