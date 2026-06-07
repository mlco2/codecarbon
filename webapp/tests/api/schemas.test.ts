import { describe, it, expect } from "vitest";
import { ProjectSchema, ExperimentSchema } from "@/api/schemas";

describe("ProjectSchema", () => {
    // Backend speaks snake_case; the rest of the app expects camelCase.
    // The transform is the contract between the two — regressions here
    // surface as "no graphs" because every project read returns null.
    it("translates organization_id (wire) into organizationId (app)", () => {
        const wire = {
            id: "p1",
            name: "Project",
            description: "desc",
            public: true,
            organization_id: "o1",
            experiments: ["e1"],
        };
        const parsed = ProjectSchema.parse(wire);
        expect(parsed.organizationId).toBe("o1");
        expect(parsed.public).toBe(true);
        expect(parsed.experiments).toEqual(["e1"]);
    });

    it("defaults nullish public/experiments coming from the backend", () => {
        const wire = {
            id: "p1",
            name: "Project",
            description: "desc",
            organization_id: "o1",
            // public and experiments are Optional[...] on the backend
        };
        const parsed = ProjectSchema.parse(wire);
        expect(parsed.public).toBe(false);
        expect(parsed.experiments).toEqual([]);
    });

    it("rejects payloads missing organization_id", () => {
        const wire = {
            id: "p1",
            name: "Project",
            description: "desc",
        };
        const r = ProjectSchema.safeParse(wire);
        expect(r.success).toBe(false);
    });
});

describe("ExperimentSchema", () => {
    it("requires a non-empty id", () => {
        const r = ExperimentSchema.safeParse({
            id: "",
            name: "exp",
            description: "",
            project_id: "p1",
        });
        expect(r.success).toBe(false);
    });

    it("accepts a populated experiment", () => {
        const r = ExperimentSchema.safeParse({
            id: "e1",
            name: "exp",
            description: "",
            project_id: "p1",
        });
        expect(r.success).toBe(true);
    });
});
