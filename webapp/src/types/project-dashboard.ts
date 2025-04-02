import { DateRange } from "react-day-picker";
import { Project } from "./project";

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
    experimentsData: {
        projectId: string;
        startDate: string;
        endDate: string;
    };
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
    organizationId: string;
}
