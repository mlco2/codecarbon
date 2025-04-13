import { DateRange } from "react-day-picker";
import { Project } from "./project";
import { ExperimentReport } from "./experiment-report";
import { Experiment } from "./experiment";

export interface RadialChartData {
    energy: { label: string; value: number };
    emissions: { label: string; value: number };
    duration: { label: string; value: number };
}

export interface ConvertedValues {
    citizen: string;
    transportation: string;
    tvTime: string;
}

export interface ProjectDashboardProps {
    project: Project;
    date: DateRange;
    onDateChange: (newDate: DateRange | undefined) => void;
    radialChartData: RadialChartData;
    convertedValues: ConvertedValues;
    experimentsReportData: ExperimentReport[];
    projectExperiments: Experiment[];
    runData: {
        experimentId: string;
        startDate: string;
        endDate: string;
    };
    selectedExperimentId: string;
    selectedRunId: string;
    onExperimentClick: (experimentId: string) => void;
    onRunClick: (runId: string) => void;
    onSettingsClick: () => void;
    isLoading?: boolean;
}
