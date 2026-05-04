import {
    MOCK_EMISSIONS_BY_RUN,
    MOCK_EXPERIMENTS,
    MOCK_EXPERIMENT_REPORTS,
    MOCK_ORGANIZATIONS,
    MOCK_ORGANIZATION_REPORT,
    MOCK_PROJECTS,
    MOCK_PROJECT_TOKENS,
    MOCK_RUNS,
    MOCK_RUN_METADATA,
    MOCK_USER,
} from "./data";

export type MockResponse = { status: number; body?: unknown };

type Handler = (params: {
    pathname: string;
    method: string;
    searchParams: URLSearchParams;
    body?: unknown;
}) => MockResponse | undefined;

const ok = (body: unknown): MockResponse => ({ status: 200, body });
const noContent = (): MockResponse => ({ status: 204 });

const handlers: Handler[] = [
    ({ pathname, method }) => {
        if (method === "GET" && pathname === "/auth/check") {
            return ok({ user: MOCK_USER });
        }
        return undefined;
    },

    ({ pathname, method }) => {
        if (method === "GET" && pathname === "/organizations") {
            return ok(MOCK_ORGANIZATIONS);
        }
        const sumsMatch = pathname.match(/^\/organizations\/([^/]+)\/sums$/);
        if (method === "GET" && sumsMatch) {
            return ok(MOCK_ORGANIZATION_REPORT);
        }
        return undefined;
    },

    ({ pathname, method, searchParams }) => {
        if (method === "GET" && pathname === "/projects") {
            const orgId = searchParams.get("organization");
            const projects = orgId
                ? MOCK_PROJECTS.filter((p) => p.organizationId === orgId)
                : MOCK_PROJECTS;
            return ok(projects);
        }
        const oneMatch = pathname.match(/^\/projects\/([^/]+)$/);
        if (method === "GET" && oneMatch) {
            const project = MOCK_PROJECTS.find((p) => p.id === oneMatch[1]);
            return project
                ? ok(project)
                : { status: 404, body: { detail: "Not found" } };
        }
        return undefined;
    },

    ({ pathname, method }) => {
        const expMatch = pathname.match(/^\/projects\/([^/]+)\/experiments$/);
        if (method === "GET" && expMatch) {
            return ok(
                MOCK_EXPERIMENTS.filter((e) => e.project_id === expMatch[1]),
            );
        }
        const sumsMatch = pathname.match(
            /^\/projects\/([^/]+)\/experiments\/sums$/,
        );
        if (method === "GET" && sumsMatch) {
            const projectExpIds = MOCK_EXPERIMENTS.filter(
                (e) => e.project_id === sumsMatch[1],
            ).map((e) => e.id);
            return ok(
                MOCK_EXPERIMENT_REPORTS.filter((r) =>
                    projectExpIds.includes(r.experiment_id),
                ),
            );
        }
        return undefined;
    },

    ({ pathname, method }) => {
        const sumsMatch = pathname.match(
            /^\/experiments\/([^/]+)\/runs\/sums$/,
        );
        if (method === "GET" && sumsMatch) {
            return ok(
                MOCK_RUNS.filter((r) => r.experiment_id === sumsMatch[1]),
            );
        }
        return undefined;
    },

    ({ pathname, method }) => {
        const runMeta = pathname.match(/^\/runs\/([^/]+)$/);
        if (method === "GET" && runMeta) {
            const meta = MOCK_RUN_METADATA[runMeta[1]];
            return meta
                ? ok(meta)
                : { status: 404, body: { detail: "Not found" } };
        }
        const runEm = pathname.match(/^\/runs\/([^/]+)\/emissions$/);
        if (method === "GET" && runEm) {
            const emissions = MOCK_EMISSIONS_BY_RUN[runEm[1]] ?? [];
            return ok({
                items: emissions.map((e) => ({
                    run_id: runEm[1],
                    timestamp: e.timestamp,
                    emissions_sum: e.emissions_sum,
                    emissions_rate: e.emissions_rate,
                    cpu_power: e.cpu_power,
                    gpu_power: e.gpu_power,
                    ram_power: e.ram_power,
                    cpu_energy: e.cpu_energy,
                    gpu_energy: e.gpu_energy,
                    ram_energy: e.ram_energy,
                    energy_consumed: e.energy_consumed,
                })),
            });
        }
        return undefined;
    },

    ({ pathname, method }) => {
        const tokensMatch = pathname.match(/^\/projects\/([^/]+)\/api-tokens$/);
        if (method === "GET" && tokensMatch) {
            return ok(MOCK_PROJECT_TOKENS[tokensMatch[1]] ?? []);
        }
        if (method === "POST" && tokensMatch) {
            return ok({
                id: `mock-token-${Date.now()}`,
                project_id: tokensMatch[1],
                name: "New mock token",
                token: "mock_newxxxxxxxxxxxxxxxxxxxxxxxxx",
                access: 2,
                last_used: null,
            });
        }
        const tokenItem = pathname.match(
            /^\/projects\/([^/]+)\/api-tokens\/([^/]+)$/,
        );
        if (method === "DELETE" && tokenItem) {
            return noContent();
        }
        return undefined;
    },
];

export function resolveMock(
    url: URL,
    method: string,
    body?: unknown,
): MockResponse {
    for (const h of handlers) {
        const r = h({
            pathname: url.pathname,
            method: method.toUpperCase(),
            searchParams: url.searchParams,
            body,
        });
        if (r !== undefined) return r;
    }
    return {
        status: 404,
        body: { detail: `No mock for ${method} ${url.pathname}` },
    };
}
