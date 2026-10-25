import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it, expect } from "vitest";

function readEnv(file: string): Record<string, string> {
    const text = readFileSync(path.resolve(__dirname, "../..", file), "utf8");
    return Object.fromEntries(
        text
            .split("\n")
            .map((line) => line.trim())
            .filter((line) => line && !line.startsWith("#"))
            .map((line) => {
                const i = line.indexOf("=");
                return [line.slice(0, i), line.slice(i + 1)];
            }),
    );
}

describe("committed env files", () => {
    it.each([".env.development", ".env.example"])(
        "%s leaves Matomo off, so local runs never reach production analytics",
        (file) => {
            const env = readEnv(file);
            expect(env.VITE_MATOMO_URL).toBe("");
            expect(env.VITE_MATOMO_SITE_ID).toBe("");
        },
    );
});
