import { ExperimentReport } from "@/types/experiment-report";
import { DateRange } from "react-day-picker";

export async function getProjectEmissionsByExperiment(
    projectId: string,
    dateRange: DateRange,
): Promise<ExperimentReport[]> {
    let url = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/experiments/sums`;

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

    const res = await fetch(url);
    const result = await res.json();
    return result.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            name: experimentReport.name,
            emissions: experimentReport.emissions,
            energy_consumed: experimentReport.energy_consumed,
            duration: experimentReport.duration,
        };
    });
}
