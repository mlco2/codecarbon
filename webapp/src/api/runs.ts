import { z } from "zod";
import { fetchApi } from "./client";
import {
    Emission,
    EmissionsTimeSeries,
    RunMetadata,
    RunMetadataSchema,
    RunReport,
} from "./schemas";

export async function getRunMetadata(
    runId: string,
): Promise<RunMetadata | null> {
    try {
        return await fetchApi(`/runs/${runId}`, RunMetadataSchema);
    } catch (error) {
        console.error("[getRunMetadata] failed", error);
        return null;
    }
}

export async function getRunEmissionsByExperiment(
    experimentId: string,
    startDate: string,
    endDate: string,
): Promise<RunReport[]> {
    if (!experimentId || experimentId === "") {
        return [];
    }

    try {
        const result = await fetchApi(
            `/experiments/${experimentId}/runs/sums?start_date=${startDate}&end_date=${endDate}`,
            z.array(
                z.object({
                    run_id: z.string(),
                    emissions: z.number(),
                    timestamp: z.string(),
                    energy_consumed: z.number(),
                    duration: z.number(),
                }),
            ),
        );

        return result.map((runReport) => ({
            runId: runReport.run_id,
            emissions: runReport.emissions,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed,
            duration: runReport.duration,
        }));
    } catch (error) {
        console.error("[getRunEmissionsByExperiment] failed", error);
        return [];
    }
}

export async function getEmissionsTimeSeries(
    runId: string,
): Promise<EmissionsTimeSeries> {
    try {
        const [runMetadataData, emissionsData] = await Promise.all([
            fetchApi(`/runs/${runId}`, RunMetadataSchema),
            fetchApi(
                `/runs/${runId}/emissions`,
                z.object({
                    items: z.array(
                        z.object({
                            run_id: z.string(),
                            timestamp: z.string(),
                            emissions_sum: z.number(),
                            emissions_rate: z.number(),
                            cpu_power: z.number(),
                            gpu_power: z.number(),
                            ram_power: z.number(),
                            cpu_energy: z.number(),
                            gpu_energy: z.number(),
                            ram_energy: z.number(),
                            energy_consumed: z.number(),
                        }),
                    ),
                }),
            ),
        ]);

        const emissions: Emission[] = emissionsData.items.map((item) => ({
            ...item,
            emission_id: item.run_id,
        }));

        return { runId, emissions, metadata: runMetadataData };
    } catch (error) {
        console.error("[getEmissionsTimeSeries] failed", error);
        return { runId, emissions: [], metadata: null };
    }
}
