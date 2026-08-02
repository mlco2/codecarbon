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

// Backend returns snake_case keys (`organization_id`); the rest of the
// codebase consumes camelCase (`organizationId`). Zod's `.transform` lets
// us validate the wire shape and expose the camelCase shape to the app.
// `public` and `experiments` are nullable on the backend (`Optional[...]`),
// so we accept undefined/null and default them.
export const ProjectSchema = z
    .object({
        id: z.string(),
        name: z.string(),
        description: z.string(),
        public: z.boolean().nullish(),
        organization_id: z.string(),
        experiments: z.array(z.string()).nullish(),
    })
    .transform((p) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        public: p.public ?? false,
        organizationId: p.organization_id,
        experiments: p.experiments ?? [],
    }));
export type Project = z.infer<typeof ProjectSchema>;

export const ProjectInputsSchema = z.object({
    name: z.string(),
    description: z.string(),
    public: z.boolean(),
});
export type ProjectInputs = z.infer<typeof ProjectInputsSchema>;

// `token` is only populated on creation; list responses serialize it as null.
export const ProjectTokenSchema = z.object({
    id: z.string(),
    project_id: z.string(),
    last_used: z.string().nullish(),
    name: z.string().nullish(),
    token: z.string().nullish(),
    access: z.number(),
    revoked: z.boolean().nullish(),
});
export type IProjectToken = z.infer<typeof ProjectTokenSchema>;

export const AccessLevel = {
    READ: 1,
    WRITE: 2,
    READ_WRITE: 3,
} as const;
export type AccessLevel = (typeof AccessLevel)[keyof typeof AccessLevel];

// Backend's `Optional[...]` fields are serialized as JSON `null` (Pydantic
// default, no `exclude_none`). Zod's `.optional()` accepts `undefined`
// only — `.nullish()` accepts `null | undefined`, which is what we need
// for every column the backend marks as nullable.
export const ExperimentSchema = z.object({
    id: z.string().min(1),
    timestamp: z.string().nullish(),
    name: z.string(),
    description: z.string(),
    on_cloud: z.boolean().nullish(),
    project_id: z.string(),
    country_name: z.string().nullish(),
    country_iso_code: z.string().nullish(),
    region: z.string().nullish(),
    cloud_provider: z.string().nullish(),
    cloud_region: z.string().nullish(),
});
export type Experiment = z.infer<typeof ExperimentSchema>;

export const ExperimentInputSchema = ExperimentSchema.extend({
    id: z.string().min(1).optional(),
});
export type ExperimentInput = z.infer<typeof ExperimentInputSchema>;

export const ExperimentReportSchema = z.object({
    experiment_id: z.string(),
    name: z.string(),
    emissions: z.number(),
    energy_consumed: z.number(),
    duration: z.number(),
    description: z.string().nullish(),
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
    os: z.string().nullish(),
    python_version: z.string().nullish(),
    codecarbon_version: z.string().nullish(),
    cpu_count: z.number().nullish(),
    cpu_model: z.string().nullish(),
    gpu_count: z.number().nullish(),
    gpu_model: z.string().nullish(),
    longitude: z.number().nullish(),
    latitude: z.number().nullish(),
    region: z.string().nullish(),
    provider: z.string().nullish(),
    ram_total_size: z.number().nullish(),
    tracking_mode: z.string().nullish(),
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
    onDateChange: (
        newDate: import("react-day-picker").DateRange | undefined,
    ) => void;
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
    onDateChange: (
        newDate: import("react-day-picker").DateRange | undefined,
    ) => void;
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
