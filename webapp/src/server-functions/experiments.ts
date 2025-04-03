import { Experiment } from "@/types/experiment";
import { ExperimentReport } from "@/types/experiment-report";
import { fetchApi } from "@/utils/api";
import { DateRange } from "react-day-picker";

export async function createExperiment(
    experiment: Experiment,
): Promise<Experiment> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/experiments`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            ...experiment,
        }),
    });

    if (!res.ok) {
        throw new Error("Failed to create experiment");
    }

    const result = await res.json();
    return result;
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
    return result?.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            name: experimentReport.name,
            emissions: experimentReport.emissions,
            energy_consumed: experimentReport.energy_consumed,
            duration: experimentReport.duration,
        };
    });
}
