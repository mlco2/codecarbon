import { Experiment } from "@/types/experiment";
import { ExperimentReport } from "@/types/experiment-report";
import { fetchApi } from "@/utils/api";
import { DateRange } from "react-day-picker";

export async function createExperiment(
    experiment: Experiment,
): Promise<Experiment> {
    const result = await fetchApi<Experiment>("/experiments", {
        method: "POST",
        body: JSON.stringify(experiment),
    });

    if (!result) {
        throw new Error("Failed to create experiment");
    }

    return result;
}
export async function getExperiments(projectId: string): Promise<Experiment[]> {
    const result = await fetchApi<Experiment[]>(
        `/projects/${projectId}/experiments`,
    );

    if (!result) {
        return [];
    }

    return result.map((experiment: Experiment) => {
        return {
            id: experiment.id,
            name: experiment.name,
            description: experiment.description,
            project_id: experiment.project_id,
            created_at: experiment.timestamp,
        };
    });
}
export async function getProjectEmissionsByExperiment(
    projectId: string,
    dateRange: DateRange,
): Promise<ExperimentReport[]> {
    let url = `/projects/${projectId}/experiments/sums`;

    if (dateRange?.from || dateRange?.to) {
        const params = new URLSearchParams();
        if (dateRange.from) {
            params.append("start_date", dateRange.from.toISOString());
        }
        if (dateRange.to) {
            params.append("end_date", dateRange.to.toISOString());
        }
        url += `?${params.toString()}`;
    }

    const result = await fetchApi<ExperimentReport[]>(url, {});
    if (!result) {
        return [];
    }

    return result.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            description: experimentReport.description,
            name: experimentReport.name,
            emissions: experimentReport.emissions,
            energy_consumed: experimentReport.energy_consumed,
            duration: experimentReport.duration,
        };
    });
}
