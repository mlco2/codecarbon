import { RunReport } from "@/types/run-report";

export async function getRunEmissionsByExperiment(
    experimentId: string,
    startDate: string,
    endDate: string,
): Promise<RunReport[]> {
    if (!experimentId || experimentId == "") {
        return [];
    }

    const url = `${process.env.NEXT_PUBLIC_API_URL}/experiments/${experimentId}/runs/sums?start_date=${startDate}&end_date=${endDate}`;
    const res = await fetch(url);

    if (!res.ok) {
        // Log error waiting for a better error management
        console.log("Failed to fetch data");
        return [];
    }
    const result = await res.json();
    return result.map((runReport: RunReport) => {
        return {
            runId: runReport.run_id,
            emissions: runReport.emissions,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed,
            duration: runReport.duration,
        };
    });
}
