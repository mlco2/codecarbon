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

// ─── Aggregate root: Organization ──────────────────────────────────────────
//
// All mock data hangs off a single organization. Object identities are
// declared in one place (`ID`) and every nested object references them by
// name, so renaming a single ID propagates through the whole graph and
// stale cross-references become a TypeScript error.
//
// Layout follows the domain hierarchy:
//
//     Organization
//        ├─ Users (members)
//        ├─ OrganizationReport (sums across all projects)
//        └─ Projects
//              ├─ ProjectTokens
//              └─ Experiments
//                    ├─ ExperimentReports (sums across runs)
//                    └─ Runs
//                          ├─ RunMetadata
//                          └─ Emissions (time series)
//

export const ID = {
    org: "mock-org-1",
    users: {
        admin: "mock-user-admin",
        member: "mock-user-member",
    },
    projects: {
        training: "mock-project-1",
        inference: "mock-project-2",
    },
    experiments: {
        baseline: "mock-experiment-1",
        optimized: "mock-experiment-2",
        production: "mock-experiment-3",
    },
    runs: {
        baseline1: "mock-run-1",
        baseline2: "mock-run-2",
        optimized1: "mock-run-3",
    },
    tokens: {
        ci: "mock-token-1",
    },
} as const;

// Wire shape (snake_case) for mock Project payloads — matches what the
// backend sends, so the same zod transform path runs in mock mode.
export interface MockProjectWire {
    id: string;
    name: string;
    description: string;
    public: boolean;
    organization_id: string;
    experiments: string[];
}

// ─── Factories ─────────────────────────────────────────────────────────────

function makeOrganization(args: {
    id: string;
    name: string;
    description: string;
}): Organization {
    return { ...args };
}

function makeUser(args: {
    id: string;
    name: string;
    email: string;
    organizationId: string;
}): User {
    return {
        id: args.id,
        name: args.name,
        email: args.email,
        organizations: [args.organizationId],
        is_active: true,
    };
}

function makeProject(args: {
    id: string;
    organizationId: string;
    name: string;
    description: string;
    public: boolean;
    experiments: string[];
}): MockProjectWire {
    return {
        id: args.id,
        name: args.name,
        description: args.description,
        public: args.public,
        organization_id: args.organizationId,
        experiments: args.experiments,
    };
}

function makeExperiment(args: {
    id: string;
    projectId: string;
    name: string;
    description: string;
    timestamp: string;
    onCloud?: boolean;
    cloudProvider?: string;
    cloudRegion?: string;
}): Experiment {
    return {
        id: args.id,
        name: args.name,
        description: args.description,
        project_id: args.projectId,
        timestamp: args.timestamp,
        on_cloud: args.onCloud ?? false,
        country_name: "France",
        country_iso_code: "FRA",
        region: "Île-de-France",
        ...(args.cloudProvider ? { cloud_provider: args.cloudProvider } : {}),
        ...(args.cloudRegion ? { cloud_region: args.cloudRegion } : {}),
    };
}

function makeExperimentReport(args: {
    experimentId: string;
    name: string;
    description: string;
    emissions: number;
    energyConsumed: number;
    durationSeconds: number;
}): ExperimentReport {
    return {
        experiment_id: args.experimentId,
        name: args.name,
        description: args.description,
        emissions: args.emissions,
        energy_consumed: args.energyConsumed,
        duration: args.durationSeconds,
    };
}

function makeRunMetadata(args: {
    runId: string;
    experimentId: string;
    timestamp: string;
}): RunMetadata {
    return {
        timestamp: args.timestamp,
        experiment_id: args.experimentId,
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
    };
}

function makeEmissionSeries(args: {
    runId: string;
    samples: number;
    startedAt: Date;
}): Emission[] {
    return Array.from({ length: args.samples }, (_, i) => {
        const ts = new Date(args.startedAt.getTime() + i * 5 * 60_000);
        return {
            emission_id: `${args.runId}-emission-${i}`,
            timestamp: ts.toISOString(),
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
    });
}

function makeProjectToken(args: {
    id: string;
    projectId: string;
    name: string;
    lastUsed: string | null;
}): IProjectToken {
    return {
        id: args.id,
        project_id: args.projectId,
        name: args.name,
        token: `mock_${args.id}_xxxxxxxxxxxxxxxxxxxxxx`,
        access: 2,
        last_used: args.lastUsed,
    };
}

export interface MockRunRow {
    run_id: string;
    experiment_id: string;
    emissions: number;
    timestamp: string;
    energy_consumed: number;
    duration: number;
}

function makeRunRow(args: {
    runId: string;
    experimentId: string;
    timestamp: string;
    emissions: number;
    energyConsumed: number;
    durationSeconds: number;
}): MockRunRow {
    return {
        run_id: args.runId,
        experiment_id: args.experimentId,
        emissions: args.emissions,
        timestamp: args.timestamp,
        energy_consumed: args.energyConsumed,
        duration: args.durationSeconds,
    };
}

// ─── Composed data (built top-down from the aggregate root) ────────────────

const organization = makeOrganization({
    id: ID.org,
    name: "Mock Organization",
    description: "Local mock organization for autonomous dev",
});

const adminUser = makeUser({
    id: ID.users.admin,
    name: "Mock Admin",
    email: "admin@codecarbon.io",
    organizationId: ID.org,
});

const memberUser = makeUser({
    id: ID.users.member,
    name: "Mock Member",
    email: "member@codecarbon.io",
    organizationId: ID.org,
});

const organizationReport: OrganizationReport = {
    name: organization.name,
    emissions: 1.801,
    energy_consumed: 8.023,
    duration: 5400,
};

const projectTraining = makeProject({
    id: ID.projects.training,
    organizationId: ID.org,
    name: "ML Training Pipeline",
    description: "Carbon footprint of our flagship training pipeline",
    public: false,
    experiments: [ID.experiments.baseline, ID.experiments.optimized],
});

const projectInference = makeProject({
    id: ID.projects.inference,
    organizationId: ID.org,
    name: "Inference Service",
    description: "Production inference emissions",
    public: true,
    experiments: [ID.experiments.production],
});

const experimentBaseline = makeExperiment({
    id: ID.experiments.baseline,
    projectId: ID.projects.training,
    name: "Baseline run",
    description: "First experiment baseline",
    timestamp: "2026-04-01T10:00:00Z",
});

const experimentOptimized = makeExperiment({
    id: ID.experiments.optimized,
    projectId: ID.projects.training,
    name: "Optimized model",
    description: "Quantized variant",
    timestamp: "2026-04-15T10:00:00Z",
    onCloud: true,
    cloudProvider: "aws",
    cloudRegion: "eu-west-3",
});

const experimentProduction = makeExperiment({
    id: ID.experiments.production,
    projectId: ID.projects.inference,
    name: "Production rollout",
    description: "Live inference",
    timestamp: "2026-04-20T10:00:00Z",
    onCloud: true,
    cloudProvider: "gcp",
    cloudRegion: "europe-west1",
});

const baselineReport = makeExperimentReport({
    experimentId: ID.experiments.baseline,
    name: experimentBaseline.name,
    description: experimentBaseline.description,
    emissions: 1.234,
    energyConsumed: 5.678,
    durationSeconds: 3600,
});

const optimizedReport = makeExperimentReport({
    experimentId: ID.experiments.optimized,
    name: experimentOptimized.name,
    description: experimentOptimized.description,
    emissions: 0.567,
    energyConsumed: 2.345,
    durationSeconds: 1800,
});

const runBaseline1 = makeRunRow({
    runId: ID.runs.baseline1,
    experimentId: ID.experiments.baseline,
    timestamp: "2026-04-01T10:00:00Z",
    emissions: 0.617,
    energyConsumed: 2.839,
    durationSeconds: 1800,
});

const runBaseline2 = makeRunRow({
    runId: ID.runs.baseline2,
    experimentId: ID.experiments.baseline,
    timestamp: "2026-04-01T11:00:00Z",
    emissions: 0.617,
    energyConsumed: 2.839,
    durationSeconds: 1800,
});

const runOptimized1 = makeRunRow({
    runId: ID.runs.optimized1,
    experimentId: ID.experiments.optimized,
    timestamp: "2026-04-15T10:00:00Z",
    emissions: 0.567,
    energyConsumed: 2.345,
    durationSeconds: 1800,
});

const ciToken = makeProjectToken({
    id: ID.tokens.ci,
    projectId: ID.projects.training,
    name: "Local dev token",
    lastUsed: "2026-04-30T08:00:00Z",
});

// ─── Exported aggregate (consumed by handlers.ts) ──────────────────────────

export const MOCK = {
    user: adminUser,

    organization: {
        list: [organization],
        byId: {
            [organization.id]: organization,
        } as Record<string, Organization>,
        report: organizationReport,
        usersByOrgId: {
            [organization.id]: [adminUser, memberUser],
        } as Record<string, User[]>,
    },

    project: {
        list: [projectTraining, projectInference],
        byId: {
            [projectTraining.id]: projectTraining,
            [projectInference.id]: projectInference,
        } as Record<string, MockProjectWire>,
        byOrgId: {
            [ID.org]: [projectTraining, projectInference],
        } as Record<string, MockProjectWire[]>,
    },

    experiment: {
        list: [experimentBaseline, experimentOptimized, experimentProduction],
        byProjectId: {
            [ID.projects.training]: [experimentBaseline, experimentOptimized],
            [ID.projects.inference]: [experimentProduction],
        } as Record<string, Experiment[]>,
        reportsByProjectId: {
            [ID.projects.training]: [baselineReport, optimizedReport],
            [ID.projects.inference]: [] as ExperimentReport[],
        } as Record<string, ExperimentReport[]>,
    },

    run: {
        byExperimentId: {
            [ID.experiments.baseline]: [runBaseline1, runBaseline2],
            [ID.experiments.optimized]: [runOptimized1],
            [ID.experiments.production]: [] as MockRunRow[],
        } as Record<string, MockRunRow[]>,
        metadataById: {
            [ID.runs.baseline1]: makeRunMetadata({
                runId: ID.runs.baseline1,
                experimentId: ID.experiments.baseline,
                timestamp: runBaseline1.timestamp,
            }),
            [ID.runs.baseline2]: makeRunMetadata({
                runId: ID.runs.baseline2,
                experimentId: ID.experiments.baseline,
                timestamp: runBaseline2.timestamp,
            }),
            [ID.runs.optimized1]: makeRunMetadata({
                runId: ID.runs.optimized1,
                experimentId: ID.experiments.optimized,
                timestamp: runOptimized1.timestamp,
            }),
        } as Record<string, RunMetadata>,
        emissionsById: {
            [ID.runs.baseline1]: makeEmissionSeries({
                runId: ID.runs.baseline1,
                samples: 12,
                startedAt: new Date(runBaseline1.timestamp),
            }),
            [ID.runs.baseline2]: makeEmissionSeries({
                runId: ID.runs.baseline2,
                samples: 12,
                startedAt: new Date(runBaseline2.timestamp),
            }),
            [ID.runs.optimized1]: makeEmissionSeries({
                runId: ID.runs.optimized1,
                samples: 6,
                startedAt: new Date(runOptimized1.timestamp),
            }),
        } as Record<string, Emission[]>,
    },

    token: {
        byProjectId: {
            [ID.projects.training]: [ciToken],
            [ID.projects.inference]: [] as IProjectToken[],
        } as Record<string, IProjectToken[]>,
    },
} as const;
