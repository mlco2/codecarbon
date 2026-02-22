import { fetchApi } from "./client";
import {
    Experiment,
    ExperimentInput,
    ExperimentSchema,
    ExperimentReport,
    ExperimentReportSchema,
} from "./schemas";
import { DateRange } from "react-day-picker";

export async function createExperiment(
    experiment: ExperimentInput,
): Promise<Experiment> {
    return await fetchApi("/experiments", ExperimentSchema, {
        method: "POST",
        body: JSON.stringify(experiment),
    });
}

export async function getExperiments(projectId: string): Promise<Experiment[]> {
    try {
        return await fetchApi(
            `/projects/${projectId}/experiments`,
            ExperimentSchema.array(),
        );
    } catch (error) {
        console.error("[getExperiments] failed", error);
        return [];
    }
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

    try {
        return await fetchApi(url, ExperimentReportSchema.array());
    } catch (error) {
        console.error("[getProjectEmissionsByExperiment] failed", error);
        return [];
    }
}
