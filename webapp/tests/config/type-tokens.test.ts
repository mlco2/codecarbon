import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { describe, it, expect } from "vitest";

const SRC = path.resolve(__dirname, "../../src");

function sourceFiles(dir: string): string[] {
    return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) return sourceFiles(full);
        return /\.(tsx?|css)$/.test(entry.name) ? [full] : [];
    });
}

describe("type tokens", () => {
    // AGENTS.md: "No hardcoded hex or font sizes"; sizes live in globals.css.
    it("sets no font size in px through an arbitrary Tailwind class", () => {
        const offenders = sourceFiles(SRC).filter((file) =>
            /\btext-\[\d+(\.\d+)?px\]/.test(readFileSync(file, "utf8")),
        );
        expect(offenders.map((f) => path.relative(SRC, f))).toEqual([]);
    });
});
