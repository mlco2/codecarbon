import { ID, MOCK, MockProjectWire } from "./data";

export type MockResponse = { status: number; body?: unknown };

type Handler = (params: {
    pathname: string;
    method: string;
    searchParams: URLSearchParams;
    body?: unknown;
}) => MockResponse | undefined;

const ok = (body: unknown): MockResponse => ({ status: 200, body });
const created = (body: unknown): MockResponse => ({ status: 201, body });
const noContent = (): MockResponse => ({ status: 204 });
const notFound = (msg = "Not found"): MockResponse => ({
    status: 404,
    body: { detail: msg },
});

const handlers: Handler[] = [
    // ─── Auth ──────────────────────────────────────────────────────────────
    ({ pathname, method }) => {
        if (method === "GET" && pathname === "/auth/check") {
            return ok({ user: MOCK.user });
        }
        return undefined;
    },

    // ─── Organizations ─────────────────────────────────────────────────────
    ({ pathname, method, body }) => {
        if (method === "GET" && pathname === "/organizations") {
            return ok(MOCK.organization.list);
        }
        if (method === "POST" && pathname === "/organizations") {
            const input = (body ?? {}) as {
                name?: string;
                description?: string;
            };
            return created({
                id: `mock-org-${Date.now()}`,
                name: input.name ?? "New org",
                description: input.description ?? "",
            });
        }
        const byId = pathname.match(/^\/organizations\/([^/]+)$/);
        if (method === "GET" && byId) {
            const org = MOCK.organization.byId[byId[1]];
            return org ? ok(org) : notFound();
        }
        const sums = pathname.match(/^\/organizations\/([^/]+)\/sums$/);
        if (method === "GET" && sums) {
            return ok(MOCK.organization.report);
        }
        const users = pathname.match(/^\/organizations\/([^/]+)\/users$/);
        if (method === "GET" && users) {
            return ok(MOCK.organization.usersByOrgId[users[1]] ?? []);
        }
        const addUser = pathname.match(/^\/organizations\/([^/]+)\/add-user$/);
        if (method === "POST" && addUser) {
            const input = (body ?? {}) as { email?: string };
            return created({
                id: `mock-user-${Date.now()}`,
                name: input.email?.split("@")[0] ?? "New user",
                email: input.email ?? "new@codecarbon.io",
                organizations: [addUser[1]],
                is_active: true,
            });
        }
        return undefined;
    },

    // ─── Projects ──────────────────────────────────────────────────────────
    ({ pathname, method, searchParams, body }) => {
        if (method === "GET" && pathname === "/projects") {
            const orgId = searchParams.get("organization");
            const projects = orgId
                ? (MOCK.project.byOrgId[orgId] ?? [])
                : MOCK.project.list;
            return ok(projects);
        }
        if (method === "POST" && pathname === "/projects") {
            const input = (body ?? {}) as Partial<MockProjectWire> & {
                organization_id?: string;
            };
            return created({
                id: `mock-project-${Date.now()}`,
                name: input.name ?? "New project",
                description: input.description ?? "",
                public: input.public ?? false,
                organization_id: input.organization_id ?? ID.org,
                experiments: [],
            });
        }
        const byId = pathname.match(/^\/projects\/([^/]+)$/);
        if (byId && byId[1] !== "public") {
            const project = MOCK.project.byId[byId[1]];
            if (method === "GET") return project ? ok(project) : notFound();
            if (method === "PATCH" && project) {
                const patch = (body ?? {}) as Partial<MockProjectWire>;
                return ok({ ...project, ...patch });
            }
            if (method === "DELETE") return noContent();
        }
        return undefined;
    },

    // ─── Experiments ───────────────────────────────────────────────────────
    ({ pathname, method, body }) => {
        if (method === "POST" && pathname === "/experiments") {
            const input = (body ?? {}) as Partial<{
                name: string;
                description: string;
                project_id: string;
                on_cloud: boolean;
            }>;
            return created({
                id: `mock-experiment-${Date.now()}`,
                name: input.name ?? "New experiment",
                description: input.description ?? "",
                project_id: input.project_id ?? ID.projects.training,
                on_cloud: input.on_cloud ?? false,
                timestamp: new Date().toISOString(),
            });
        }
        const list = pathname.match(/^\/projects\/([^/]+)\/experiments$/);
        if (method === "GET" && list) {
            return ok(MOCK.experiment.byProjectId[list[1]] ?? []);
        }
        const sums = pathname.match(/^\/projects\/([^/]+)\/experiments\/sums$/);
        if (method === "GET" && sums) {
            return ok(MOCK.experiment.reportsByProjectId[sums[1]] ?? []);
        }
        return undefined;
    },

    // ─── Runs ──────────────────────────────────────────────────────────────
    ({ pathname, method }) => {
        const sums = pathname.match(/^\/experiments\/([^/]+)\/runs\/sums$/);
        if (method === "GET" && sums) {
            return ok(MOCK.run.byExperimentId[sums[1]] ?? []);
        }
        const meta = pathname.match(/^\/runs\/([^/]+)$/);
        if (method === "GET" && meta) {
            const m = MOCK.run.metadataById[meta[1]];
            return m ? ok(m) : notFound();
        }
        const emissions = pathname.match(/^\/runs\/([^/]+)\/emissions$/);
        if (method === "GET" && emissions) {
            const items = (MOCK.run.emissionsById[emissions[1]] ?? []).map(
                (e) => ({
                    run_id: emissions[1],
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
                }),
            );
            return ok({ items });
        }
        return undefined;
    },

    // ─── Project tokens ────────────────────────────────────────────────────
    ({ pathname, method }) => {
        const list = pathname.match(/^\/projects\/([^/]+)\/api-tokens$/);
        if (method === "GET" && list) {
            return ok(MOCK.token.byProjectId[list[1]] ?? []);
        }
        if (method === "POST" && list) {
            return created({
                id: `mock-token-${Date.now()}`,
                project_id: list[1],
                name: "New mock token",
                token: "mock_newxxxxxxxxxxxxxxxxxxxxxxxxx",
                access: 2,
                last_used: null,
            });
        }
        const item = pathname.match(
            /^\/projects\/([^/]+)\/api-tokens\/([^/]+)$/,
        );
        if (method === "DELETE" && item) {
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
