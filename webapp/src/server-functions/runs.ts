import { Emission } from "@/types/emission";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";
import { RunMetadata } from "@/types/run-metadata";
import { fetchApi } from "@/utils/api";
import { RunReport } from "@/types/run-report";

export async function getRunMetadata(runId: string): Promise<RunMetadata> {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/runs/${runId}`;
    const res = await fetch(url);
    return await res.json();
}

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
    return result.map((runReport: any) => {
        return {
            runId: runReport.run_id,
            emissions: runReport.emissions,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed,
            duration: runReport.duration,
        };
    });
}

export async function getEmissionsTimeSeries(
    runId: string,
): Promise<EmissionsTimeSeries> {
    try {
        const runMetadataData = await fetchApi<RunMetadata>(`/runs/${runId}`);
        const emissionsData = await fetchApi<{ items: Emission[] }>(
            `/runs/${runId}/emissions`,
        );

        if (!runMetadataData || !emissionsData) {
            return {
                runId,
                emissions: [],
                metadata: null,
            };
        }

        const metadata: RunMetadata = {
            timestamp: runMetadataData.timestamp,
            experiment_id: runMetadataData.experiment_id,
            os: runMetadataData.os,
            python_version: runMetadataData.python_version,
            codecarbon_version: runMetadataData.codecarbon_version,
            cpu_count: runMetadataData.cpu_count,
            cpu_model: runMetadataData.cpu_model,
            gpu_count: runMetadataData.gpu_count,
            gpu_model: runMetadataData.gpu_model,
            longitude: runMetadataData.longitude,
            latitude: runMetadataData.latitude,
            region: runMetadataData.region,
            provider: runMetadataData.provider,
            ram_total_size: runMetadataData.ram_total_size,
            tracking_mode: runMetadataData.tracking_mode,
        };

        const emissions: Emission[] = emissionsData.items.map((item: any) => ({
            emission_id: item.run_id,
            timestamp: item.timestamp,
            emissions_sum: item.emissions_sum,
            emissions_rate: item.emissions_rate,
            cpu_power: item.cpu_power,
            gpu_power: item.gpu_power,
            ram_power: item.ram_power,
            cpu_energy: item.cpu_energy,
            gpu_energy: item.gpu_energy,
            ram_energy: item.ram_energy,
            energy_consumed: item.energy_consumed,
        }));

        return {
            runId,
            emissions,
            metadata,
        };
    } catch (error) {
        console.error("Failed to fetch emissions time series:", error);
        throw error;
    }
}
