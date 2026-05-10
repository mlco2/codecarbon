import type {
    Emission,
    Experiment,
    ExperimentReport,
    Organization,
    OrganizationReport,
    IProjectToken,
    RunMetadata,
    User,
} from "../schemas";

// Mock project payloads mirror the backend wire format (snake_case keys),
// so they exercise the same zod validation/transformation path as real
// responses.
export interface MockProjectWire {
    id: string;
    name: string;
    description: string;
    public: boolean;
    organization_id: string;
    experiments: string[];
}

export const MOCK_USER: User = {
    id: "mock-user-1",
    email: "mock@codecarbon.io",
    name: "Mock User",
    organizations: ["mock-org-1"],
    is_active: true,
};

export const MOCK_ORGANIZATIONS: Organization[] = [
    {
        id: "mock-org-1",
        name: "Mock Organization",
        description: "Local mock organization for autonomous dev",
    },
];

export const MOCK_PROJECTS: MockProjectWire[] = [
    {
        id: "mock-project-1",
        name: "ML Training Pipeline",
        description: "Carbon footprint of our flagship training pipeline",
        public: false,
        organization_id: "mock-org-1",
        experiments: ["mock-experiment-1", "mock-experiment-2"],
    },
    {
        id: "mock-project-2",
        name: "Inference Service",
        description: "Production inference emissions",
        public: true,
        organization_id: "mock-org-1",
        experiments: ["mock-experiment-3"],
    },
];

export const MOCK_EXPERIMENTS: Experiment[] = [
    {
        id: "mock-experiment-1",
        name: "Baseline run",
        description: "First experiment baseline",
        project_id: "mock-project-1",
        timestamp: "2026-04-01T10:00:00Z",
        on_cloud: false,
        country_name: "France",
        country_iso_code: "FRA",
        region: "Île-de-France",
    },
    {
        id: "mock-experiment-2",
        name: "Optimized model",
        description: "Quantized variant",
        project_id: "mock-project-1",
        timestamp: "2026-04-15T10:00:00Z",
        on_cloud: true,
        country_name: "France",
        country_iso_code: "FRA",
        region: "Île-de-France",
        cloud_provider: "aws",
        cloud_region: "eu-west-3",
    },
    {
        id: "mock-experiment-3",
        name: "Production rollout",
        description: "Live inference",
        project_id: "mock-project-2",
        timestamp: "2026-04-20T10:00:00Z",
        on_cloud: true,
        cloud_provider: "gcp",
        cloud_region: "europe-west1",
    },
];

export const MOCK_EXPERIMENT_REPORTS: ExperimentReport[] = [
    {
        experiment_id: "mock-experiment-1",
        name: "Baseline run",
        description: "First experiment baseline",
        emissions: 1.234,
        energy_consumed: 5.678,
        duration: 3600,
    },
    {
        experiment_id: "mock-experiment-2",
        name: "Optimized model",
        description: "Quantized variant",
        emissions: 0.567,
        energy_consumed: 2.345,
        duration: 1800,
    },
];

export const MOCK_ORGANIZATION_REPORT: OrganizationReport = {
    name: "Mock Organization",
    emissions: 1.801,
    energy_consumed: 8.023,
    duration: 5400,
};

export const MOCK_RUNS = [
    {
        run_id: "mock-run-1",
        experiment_id: "mock-experiment-1",
        emissions: 0.617,
        timestamp: "2026-04-01T10:00:00Z",
        energy_consumed: 2.839,
        duration: 1800,
    },
    {
        run_id: "mock-run-2",
        experiment_id: "mock-experiment-1",
        emissions: 0.617,
        timestamp: "2026-04-01T11:00:00Z",
        energy_consumed: 2.839,
        duration: 1800,
    },
    {
        run_id: "mock-run-3",
        experiment_id: "mock-experiment-2",
        emissions: 0.567,
        timestamp: "2026-04-15T10:00:00Z",
        energy_consumed: 2.345,
        duration: 1800,
    },
];

export const MOCK_RUN_METADATA: Record<string, RunMetadata> = {
    "mock-run-1": {
        timestamp: "2026-04-01T10:00:00Z",
        experiment_id: "mock-experiment-1",
        os: "Linux-6.5.0-generic-x86_64",
        python_version: "3.12.6",
        codecarbon_version: "3.0.0",
        cpu_count: 16,
        cpu_model: "Intel Xeon Platinum 8375C",
        gpu_count: 1,
        gpu_model: "NVIDIA A10G",
        longitude: 2.3522,
        latitude: 48.8566,
        region: "Île-de-France",
        provider: "aws",
        ram_total_size: 64,
        tracking_mode: "machine",
    },
};

function makeEmission(i: number, runId: string): Emission {
    const ts = new Date(2026, 3, 1, 10, i * 5).toISOString();
    return {
        emission_id: `${runId}-emission-${i}`,
        timestamp: ts,
        emissions_sum: 0.05 + i * 0.01,
        emissions_rate: 0.0001 + i * 0.00001,
        cpu_power: 65 + i,
        gpu_power: 200 + i * 2,
        ram_power: 8,
        cpu_energy: 0.1 + i * 0.01,
        gpu_energy: 0.3 + i * 0.02,
        ram_energy: 0.05,
        energy_consumed: 0.45 + i * 0.03,
    };
}

export const MOCK_EMISSIONS_BY_RUN: Record<string, Emission[]> = {
    "mock-run-1": Array.from({ length: 12 }, (_, i) =>
        makeEmission(i, "mock-run-1"),
    ),
    "mock-run-2": Array.from({ length: 12 }, (_, i) =>
        makeEmission(i, "mock-run-2"),
    ),
    "mock-run-3": Array.from({ length: 6 }, (_, i) =>
        makeEmission(i, "mock-run-3"),
    ),
};

export const MOCK_PROJECT_TOKENS: Record<string, IProjectToken[]> = {
    "mock-project-1": [
        {
            id: "mock-token-1",
            project_id: "mock-project-1",
            name: "Local dev token",
            token: "mock_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            access: 2,
            last_used: "2026-04-30T08:00:00Z",
        },
    ],
    "mock-project-2": [],
};
