import { describe, it, expect, vi, afterEach } from "vitest";
import { buildLoginUrl, redirectToLogin } from "@/api/auth";

afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
});

describe("buildLoginUrl", () => {
    it("constructs login URL with redirect using URL constructor", () => {
        const built = buildLoginUrl();
        expect(built).not.toBeNull();
        const url = new URL(built!);
        expect(url.origin + url.pathname).toBe(
            "http://api.test/api/auth/login",
        );
        expect(url.searchParams.get("redirect")).toBe(
            "http://app.test/home?auth=true",
        );
    });

    it("encodes the redirect query parameter", () => {
        const url = buildLoginUrl();
        expect(url).toContain(
            "redirect=http%3A%2F%2Fapp.test%2Fhome%3Fauth%3Dtrue",
        );
    });

    it("returns null and warns when VITE_API_URL is missing (pnpm dev with no .env)", () => {
        vi.stubEnv("VITE_API_URL", "");
        const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
        expect(buildLoginUrl()).toBeNull();
        expect(warn).toHaveBeenCalled();
    });
});

describe("redirectToLogin", () => {
    it("is a no-op when login URL cannot be built", () => {
        vi.stubEnv("VITE_API_URL", "");
        vi.spyOn(console, "warn").mockImplementation(() => {});
        const assign = vi.fn();
        // jsdom's window.location.assign is read-only; replace with a spy.
        Object.defineProperty(window, "location", {
            writable: true,
            value: { ...window.location, assign },
        });
        redirectToLogin();
        expect(assign).not.toHaveBeenCalled();
    });
});
