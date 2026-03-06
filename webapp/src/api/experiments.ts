import { fetchApi } from "./client";
import {
  Experiment,
  ExperimentSchema,
  ExperimentReport,
  ExperimentReportSchema,
} from "./schemas";
import { DateRange } from "react-day-picker";

export async function createExperiment(
  experiment: Experiment,
): Promise<Experiment> {
  return await fetchApi("/experiments", ExperimentSchema, {
    method: "POST",
    body: JSON.stringify(experiment),
  });
}

export async function getExperiments(projectId: string): Promise<Experiment[]> {
  try {
    const result = await fetchApi(
      `/projects/${projectId}/experiments`,
      ExperimentSchema.array(),
    );
    return result.map((experiment) => ({
      id: experiment.id,
      name: experiment.name,
      description: experiment.description,
      project_id: experiment.project_id,
      timestamp: experiment.timestamp,
    }));
  } catch {
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
    const result = await fetchApi(url, ExperimentReportSchema.array());
    return result.map((experimentReport) => ({
      experiment_id: experimentReport.experiment_id,
      description: experimentReport.description,
      name: experimentReport.name,
      emissions: experimentReport.emissions,
      energy_consumed: experimentReport.energy_consumed,
      duration: experimentReport.duration,
    }));
  } catch {
    return [];
  }
}
