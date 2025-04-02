import { DateRange } from "react-day-picker";
import { Project } from "./project";
import { RadialChartData, ConvertedValues } from "./project-dashboard";

export interface PublicProjectDashboardProps {
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
}