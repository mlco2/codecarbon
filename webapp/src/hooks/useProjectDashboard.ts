import { useCallback, useEffect, useState } from "react";
import { DateRange } from "react-day-picker";
import { Experiment } from "@/types/experiment";
import { ExperimentReport } from "@/types/experiment-report";
import {
    calculateConvertedValues,
    calculateRadialChartData,
    ConvertedValues,
    getDefaultConvertedValues,
    getDefaultRadialChartData,
    RadialChartData,
} from "@/helpers/dashboard-calculations";
import { getExperiments } from "@/server-functions/experiments";

export type RunData = {
    experimentId: string;
    startDate: string;
    endDate: string;
};

export type ProjectDashboardData = {
    radialChartData: RadialChartData;
    convertedValues: ConvertedValues;
    experimentsReportData: ExperimentReport[];
    projectExperiments: Experiment[];
    runData: RunData;
    selectedExperimentId: string;
    selectedRunId: string;
    isLoading: boolean;
    setSelectedExperimentId: (id: string) => void;
    setSelectedRunId: (id: string) => void;
    handleExperimentClick: (experimentId: string) => void;
    handleRunClick: (runId: string) => void;
    refreshExperimentList: () => Promise<void>;
    processReportData: (data: ExperimentReport[]) => void;
    setIsLoading: (loading: boolean) => void;
};

/**
 * Custom hook for managing project dashboard state and logic
 * Extracts common logic shared between authenticated and public dashboard pages
 */
export function useProjectDashboard(
    projectId: string | null,
    date: DateRange,
): ProjectDashboardData {
    const [isLoading, setIsLoading] = useState(true);
    const [radialChartData, setRadialChartData] = useState<RadialChartData>(
        getDefaultRadialChartData(),
    );
    const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
        [],
    );
    const [experimentsReportData, setExperimentsReportData] = useState<
        ExperimentReport[]
    >([]);
    const [runData, setRunData] = useState<RunData>({
        experimentId: "",
        startDate: date.from?.toISOString() || "",
        endDate: date.to?.toISOString() || "",
    });
    const [convertedValues, setConvertedValues] = useState<ConvertedValues>(
        getDefaultConvertedValues(),
    );
    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    const refreshExperimentList = useCallback(async () => {
        if (!projectId) return;
        const experiments: Experiment[] = await getExperiments(projectId);
        setProjectExperiments(experiments);
    }, [projectId]);

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

    /**
     * Process experiment report data and update all derived state
     */
    const processReportData = useCallback(
        (report: ExperimentReport[]) => {
            setExperimentsReportData(report);

            const newRadialChartData = calculateRadialChartData(report);
            setRadialChartData(newRadialChartData);

            setRunData({
                experimentId: report[0]?.experiment_id ?? "",
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

            setSelectedExperimentId(report[0]?.experiment_id ?? "");

            const newConvertedValues =
                calculateConvertedValues(newRadialChartData);
            setConvertedValues(newConvertedValues);
        },
        [date],
    );

    return {
        radialChartData,
        convertedValues,
        experimentsReportData,
        projectExperiments,
        runData,
        selectedExperimentId,
        selectedRunId,
        isLoading,
        setSelectedExperimentId,
        setSelectedRunId,
        handleExperimentClick,
        handleRunClick,
        refreshExperimentList,
        processReportData,
        setIsLoading,
    };
}
