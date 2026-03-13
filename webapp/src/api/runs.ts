import { z } from "zod";
import { fetchApi } from "./client";
import {
  Emission,
  EmissionSchema,
  EmissionsTimeSeries,
  RunMetadata,
  RunMetadataSchema,
  RunReport,
  RunReportSchema,
} from "./schemas";

export async function getRunMetadata(
  runId: string,
): Promise<RunMetadata | null> {
  try {
    return await fetchApi(`/runs/${runId}`, RunMetadataSchema);
  } catch {
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
      z.array(z.object({
        run_id: z.string(),
        emissions: z.number(),
        timestamp: z.string(),
        energy_consumed: z.number(),
        duration: z.number(),
      })),
    );

    return result.map((runReport) => ({
      runId: runReport.run_id,
      emissions: runReport.emissions,
      timestamp: runReport.timestamp,
      energy_consumed: runReport.energy_consumed,
      duration: runReport.duration,
    }));
  } catch {
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

    const emissions: Emission[] = emissionsData.items.map((item) => ({
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

    return { runId, emissions, metadata };
  } catch {
    return { runId, emissions: [], metadata: null };
  }
}
