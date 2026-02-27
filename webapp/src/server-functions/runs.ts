import { Emission } from "@/types/emission";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";
import { RunMetadata } from "@/types/run-metadata";
import { fetchApi } from "@/utils/api";
import { RunReport } from "@/types/run-report";

export async function getRunMetadata(
    runId: string,
): Promise<RunMetadata | null> {
    const result = await fetchApi<RunMetadata>(`/runs/${runId}`);
    return result;
}

export async function getRunEmissionsByExperiment(
    experimentId: string,
    startDate: string,
    endDate: string,
): Promise<RunReport[]> {
    if (!experimentId || experimentId == "") {
        return [];
    }

    const result = await fetchApi<RunReport[]>(
        `/experiments/${experimentId}/runs/sums?start_date=${startDate}&end_date=${endDate}`,
    );

    if (!result) {
        return [];
    }

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
    const [runMetadataData, emissionsData] = await Promise.all([
        fetchApi<RunMetadata>(`/runs/${runId}`),
        fetchApi<{ items: Emission[] }>(`/runs/${runId}/emissions`),
    ]);

    // Return empty data on failure (Pattern A - Read operation)
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
}
