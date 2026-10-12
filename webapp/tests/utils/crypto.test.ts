import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

beforeEach(() => {
    vi.stubEnv(
        "VITE_PROJECT_ENCRYPTION_KEY",
        "f1d2e3a4c5b6a78902e1f0d3c4b5a6e7",
    );
});

afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
});

describe("crypto util", () => {
    it("decrypts a legacy sharing token", async () => {
        const { decryptProjectId } = await import("@/utils/crypto");
        const token =
            "o2-eIx03_AFnlp2MGLTE3J3NbL0_x-Q7nHp8Lgnsrh0_6KUeRVLnEvnZletduYJw4ZWnigqkwP0sIRCXmJKgHA";
        await expect(decryptProjectId(token)).resolves.toBe(
            "8edb03e1-9a28-452a-9c93-a3b6560136d7",
        );
    });

    it("throws when VITE_PROJECT_ENCRYPTION_KEY is missing", async () => {
        vi.stubEnv("VITE_PROJECT_ENCRYPTION_KEY", "");
        const { decryptProjectId } = await import("@/utils/crypto");
        await expect(decryptProjectId("legacy-token")).rejects.toThrow(
            /VITE_PROJECT_ENCRYPTION_KEY/,
        );
    });

    it("rejects malformed sharing tokens", async () => {
        const { decryptProjectId } = await import("@/utils/crypto");
        await expect(decryptProjectId("too-short")).rejects.toBeDefined();
    });
});
