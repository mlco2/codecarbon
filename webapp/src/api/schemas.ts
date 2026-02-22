import { z } from "zod";

export const OrganizationSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
});
export type Organization = z.infer<typeof OrganizationSchema>;

export const UserSchema = z.object({
  id: z.string(),
  email: z.string(),
  name: z.string(),
  organizations: z.array(z.string()),
  is_active: z.boolean(),
});
export type User = z.infer<typeof UserSchema>;

export const ProjectSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  public: z.boolean(),
  organizationId: z.string(),
  experiments: z.array(z.string()),
});
export type Project = z.infer<typeof ProjectSchema>;

export const ProjectInputsSchema = z.object({
  name: z.string(),
  description: z.string(),
  public: z.boolean(),
});
export type ProjectInputs = z.infer<typeof ProjectInputsSchema>;

export const ProjectTokenSchema = z.object({
  id: z.string(),
  project_id: z.string(),
  last_used: z.string().nullable(),
  name: z.string(),
  token: z.string(),
  access: z.number(),
});
export type IProjectToken = z.infer<typeof ProjectTokenSchema>;

export const ExperimentSchema = z.object({
  id: z.string().optional(),
  timestamp: z.string().optional(),
  name: z.string(),
  description: z.string(),
  on_cloud: z.boolean().optional(),
  project_id: z.string(),
  country_name: z.string().optional(),
  country_iso_code: z.string().optional(),
  region: z.string().optional(),
  cloud_provider: z.string().optional(),
  cloud_region: z.string().optional(),
});
export type Experiment = z.infer<typeof ExperimentSchema>;

export const ExperimentReportSchema = z.object({
  experiment_id: z.string(),
  name: z.string(),
  emissions: z.number(),
  energy_consumed: z.number(),
  duration: z.number(),
  description: z.string().optional(),
});
export type ExperimentReport = z.infer<typeof ExperimentReportSchema>;

export const RunReportSchema = z.object({
  runId: z.string(),
  emissions: z.number(),
  timestamp: z.string(),
  energy_consumed: z.number(),
  duration: z.number(),
});
export type RunReport = z.infer<typeof RunReportSchema>;

export const EmissionSchema = z.object({
  emission_id: z.string(),
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
});
export type Emission = z.infer<typeof EmissionSchema>;

export const RunMetadataSchema = z.object({
  timestamp: z.string(),
  experiment_id: z.string(),
  os: z.string(),
  python_version: z.string(),
  codecarbon_version: z.string(),
  cpu_count: z.number(),
  cpu_model: z.string(),
  gpu_count: z.number(),
  gpu_model: z.string(),
  longitude: z.number(),
  latitude: z.number(),
  region: z.string(),
  provider: z.string(),
  ram_total_size: z.number(),
  tracking_mode: z.string(),
});
export type RunMetadata = z.infer<typeof RunMetadataSchema>;

export const OrganizationReportSchema = z.object({
  name: z.string(),
  emissions: z.number(),
  energy_consumed: z.number(),
  duration: z.number(),
});
export type OrganizationReport = z.infer<typeof OrganizationReportSchema>;

export const EmissionsTimeSeriesSchema = z.object({
  runId: z.string(),
  emissions: z.array(EmissionSchema),
  metadata: RunMetadataSchema.nullable(),
});
export type EmissionsTimeSeries = z.infer<typeof EmissionsTimeSeriesSchema>;

// Dashboard prop types (not API responses, but shared across components)
export interface RadialChartData {
  energy: { label: string; value: number };
  emissions: { label: string; value: number };
  duration: { label: string; value: number };
}

export interface ConvertedValues {
  citizen: string;
  transportation: string;
  tvTime: string;
}

export interface ProjectDashboardProps {
  project: Project;
  date: import("react-day-picker").DateRange;
  onDateChange: (newDate: import("react-day-picker").DateRange | undefined) => void;
  radialChartData: RadialChartData;
  convertedValues: ConvertedValues;
  experimentsReportData: ExperimentReport[];
  projectExperiments: Experiment[];
  runData: {
    experimentId: string;
    startDate: string;
    endDate: string;
  };
  selectedExperimentId: string;
  selectedRunId: string;
  onExperimentClick: (experimentId: string) => void;
  onRunClick: (runId: string) => void;
  onSettingsClick: () => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

export interface PublicProjectDashboardProps {
  project: Project;
  date: import("react-day-picker").DateRange;
  onDateChange: (newDate: import("react-day-picker").DateRange | undefined) => void;
  radialChartData: RadialChartData;
  convertedValues: ConvertedValues;
  experimentsReportData: ExperimentReport[];
  projectExperiments: Experiment[];
  runData: {
    experimentId: string;
    startDate: string;
    endDate: string;
  };
  selectedExperimentId: string;
  selectedRunId: string;
  onExperimentClick: (experimentId: string) => void;
  onRunClick: (runId: string) => void;
  isLoading?: boolean;
}
