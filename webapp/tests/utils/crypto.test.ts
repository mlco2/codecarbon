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
    it("round-trips a project id (encrypt → decrypt)", async () => {
        const { encryptProjectId, decryptProjectId } = await import(
            "@/utils/crypto"
        );
        const id = "8edb03e1-9a28-452a-9c93-a3b6560136d7";
        const token = await encryptProjectId(id);
        expect(token).not.toBe(id);
        expect(token).toMatch(/^[A-Za-z0-9_-]+$/); // base64url, no padding
        const decrypted = await decryptProjectId(token);
        expect(decrypted).toBe(id);
    });

    it("is deterministic — same id always produces the same token", async () => {
        const { encryptProjectId } = await import("@/utils/crypto");
        const id = "stable-project-id";
        const a = await encryptProjectId(id);
        const b = await encryptProjectId(id);
        expect(a).toBe(b);
    });

    it("produces different tokens for different ids", async () => {
        const { encryptProjectId } = await import("@/utils/crypto");
        const a = await encryptProjectId("project-a");
        const b = await encryptProjectId("project-b");
        expect(a).not.toBe(b);
    });

    it("rejects a token that wasn't produced with the configured key", async () => {
        const { encryptProjectId, decryptProjectId } = await import(
            "@/utils/crypto"
        );
        const token = await encryptProjectId("real-id");

        // Swap the key and try to decrypt — should throw.
        vi.stubEnv("VITE_PROJECT_ENCRYPTION_KEY", "different-key-aaaaaaaaaa");
        await expect(decryptProjectId(token)).rejects.toBeDefined();
    });

    it("throws when VITE_PROJECT_ENCRYPTION_KEY is missing", async () => {
        vi.stubEnv("VITE_PROJECT_ENCRYPTION_KEY", "");
        const { encryptProjectId } = await import("@/utils/crypto");
        await expect(encryptProjectId("anything")).rejects.toThrow(
            /VITE_PROJECT_ENCRYPTION_KEY/,
        );
    });

    it("rejects malformed sharing tokens", async () => {
        const { decryptProjectId } = await import("@/utils/crypto");
        await expect(decryptProjectId("too-short")).rejects.toBeDefined();
    });
});
