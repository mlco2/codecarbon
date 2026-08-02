import { describe, it, expect } from "vitest";
import { resolveMock } from "@/api/mock/handlers";
import { ID, MOCK } from "@/api/mock/data";

function url(path: string): URL {
    return new URL(path, "http://mock.local");
}

describe("resolveMock — auth", () => {
    it("returns the mock admin user for /auth/check", () => {
        const r = resolveMock(url("/auth/check"), "GET");
        expect(r.status).toBe(200);
        expect((r.body as { user: { email: string } }).user.email).toBe(
            MOCK.user.email,
        );
    });
});

describe("resolveMock — organizations", () => {
    it("lists organizations", () => {
        const r = resolveMock(url("/organizations"), "GET");
        expect(r.status).toBe(200);
        expect((r.body as unknown[]).length).toBe(1);
    });

    it("fetches a single organization by id", () => {
        const r = resolveMock(url(`/organizations/${ID.org}`), "GET");
        expect(r.status).toBe(200);
        expect((r.body as { id: string }).id).toBe(ID.org);
    });

    it("returns 404 for an unknown organization", () => {
        const r = resolveMock(url("/organizations/does-not-exist"), "GET");
        expect(r.status).toBe(404);
    });

    it("returns users for the mock organization", () => {
        const r = resolveMock(url(`/organizations/${ID.org}/users`), "GET");
        expect(r.status).toBe(200);
        const users = r.body as Array<{ id: string }>;
        expect(users.map((u) => u.id)).toContain(ID.users.admin);
        expect(users.map((u) => u.id)).toContain(ID.users.member);
    });

    it("returns the org sums report", () => {
        const r = resolveMock(url(`/organizations/${ID.org}/sums`), "GET");
        expect(r.status).toBe(200);
        expect((r.body as { name: string }).name).toBe("Mock Organization");
    });

    it("synthesizes an added user on POST /add-user", () => {
        const r = resolveMock(
            url(`/organizations/${ID.org}/add-user`),
            "POST",
            { email: "newbie@codecarbon.io" },
        );
        expect(r.status).toBe(201);
        expect((r.body as { email: string }).email).toBe(
            "newbie@codecarbon.io",
        );
    });
});

describe("resolveMock — projects", () => {
    it("filters projects by organization query param (snake_case wire shape)", () => {
        const r = resolveMock(url(`/projects?organization=${ID.org}`), "GET");
        expect(r.status).toBe(200);
        const projects = r.body as Array<{ organization_id: string }>;
        expect(projects.length).toBeGreaterThan(0);
        for (const p of projects) expect(p.organization_id).toBe(ID.org);
    });

    it("returns a single project by id", () => {
        const r = resolveMock(url(`/projects/${ID.projects.training}`), "GET");
        expect(r.status).toBe(200);
        expect((r.body as { id: string }).id).toBe(ID.projects.training);
    });

    it("204s on project deletion", () => {
        const r = resolveMock(
            url(`/projects/${ID.projects.training}`),
            "DELETE",
        );
        expect(r.status).toBe(204);
    });

    it("synthesizes a new project on POST", () => {
        const r = resolveMock(url("/projects"), "POST", {
            name: "Synthesized",
            description: "made by handler",
            organization_id: ID.org,
        });
        expect(r.status).toBe(201);
        const created = r.body as { name: string; organization_id: string };
        expect(created.name).toBe("Synthesized");
        expect(created.organization_id).toBe(ID.org);
    });
});

describe("resolveMock — experiments & runs", () => {
    it("lists experiments by project", () => {
        const r = resolveMock(
            url(`/projects/${ID.projects.training}/experiments`),
            "GET",
        );
        expect(r.status).toBe(200);
        const exps = r.body as Array<{ id: string }>;
        expect(exps.map((e) => e.id)).toEqual([
            ID.experiments.baseline,
            ID.experiments.optimized,
        ]);
    });

    it("returns runs by experiment", () => {
        const r = resolveMock(
            url(`/experiments/${ID.experiments.baseline}/runs/sums`),
            "GET",
        );
        expect(r.status).toBe(200);
        const runs = r.body as Array<{ run_id: string }>;
        expect(runs.length).toBe(2);
    });

    it("returns run metadata and emissions for a known run", () => {
        const meta = resolveMock(url(`/runs/${ID.runs.baseline1}`), "GET");
        expect(meta.status).toBe(200);
        expect((meta.body as { experiment_id: string }).experiment_id).toBe(
            ID.experiments.baseline,
        );

        const emissions = resolveMock(
            url(`/runs/${ID.runs.baseline1}/emissions`),
            "GET",
        );
        expect(emissions.status).toBe(200);
        const items = (emissions.body as { items: unknown[] }).items;
        expect(items.length).toBe(12);
    });
});

describe("resolveMock — fallthrough", () => {
    it("returns 404 with a useful detail for unmatched routes", () => {
        const r = resolveMock(url("/does/not/exist"), "GET");
        expect(r.status).toBe(404);
        expect((r.body as { detail: string }).detail).toContain(
            "No mock for GET /does/not/exist",
        );
    });
});

describe("MOCK aggregate consistency", () => {
    it("every project links to a known organization", () => {
        for (const project of MOCK.project.list) {
            expect(
                MOCK.organization.byId[project.organization_id],
            ).toBeDefined();
        }
    });

    it("every experiment links to a known project", () => {
        for (const exp of MOCK.experiment.list) {
            expect(MOCK.project.byId[exp.project_id]).toBeDefined();
        }
    });

    it("every run links to a known experiment", () => {
        for (const expId of Object.keys(MOCK.run.byExperimentId)) {
            expect(MOCK.experiment.list.some((e) => e.id === expId)).toBe(true);
        }
    });

    it("every run metadata links to a known experiment", () => {
        for (const meta of Object.values(MOCK.run.metadataById)) {
            expect(
                MOCK.experiment.list.some((e) => e.id === meta.experiment_id),
            ).toBe(true);
        }
    });
});
