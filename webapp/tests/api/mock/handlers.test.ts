import { describe, it, expect } from "vitest";
import { resolveMock } from "@/api/mock/handlers";
import { MOCK_PROJECTS, MOCK_USER } from "@/api/mock/data";

function url(path: string): URL {
    return new URL(path, "http://mock.local");
}

describe("resolveMock", () => {
    it("returns mock user for /auth/check", () => {
        const r = resolveMock(url("/auth/check"), "GET");
        expect(r.status).toBe(200);
        expect(
            (r as { body: { user: typeof MOCK_USER } }).body.user.email,
        ).toBe(MOCK_USER.email);
    });

    it("filters projects by organization query param", () => {
        const r = resolveMock(url("/projects?organization=mock-org-1"), "GET");
        expect(r.status).toBe(200);
        const body = (r as { body: typeof MOCK_PROJECTS }).body;
        expect(body.length).toBe(MOCK_PROJECTS.length);
        for (const p of body) expect(p.organization_id).toBe("mock-org-1");
    });

    it("returns 404 with explanation for unmatched routes", () => {
        const r = resolveMock(url("/does/not/exist"), "GET");
        expect(r.status).toBe(404);
        expect((r as { body: { detail: string } }).body.detail).toContain(
            "No mock for GET /does/not/exist",
        );
    });

    it("returns 204 for project token deletion", () => {
        const r = resolveMock(
            url("/projects/mock-project-1/api-tokens/mock-token-1"),
            "DELETE",
        );
        expect(r.status).toBe(204);
    });
});
