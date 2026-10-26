import { describe, it, expect, vi, afterEach } from "vitest";
import {
    buildAccountUrl,
    buildLoginUrl,
    buildLogoutUrl,
    redirectToAccount,
    redirectToLogin,
    redirectToLogout,
} from "@/api/auth";

afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
});

describe("buildLoginUrl", () => {
    it("constructs the login URL", () => {
        const built = buildLoginUrl();
        expect(built).not.toBeNull();
        const url = new URL(built!);
        expect(url.origin + url.pathname).toBe(
            "http://api.test/api/auth/login",
        );
        expect(url.search).toBe("");
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

describe.each([
    ["buildLogoutUrl", buildLogoutUrl, "/auth/logout", redirectToLogout],
    ["buildAccountUrl", buildAccountUrl, "/auth/account", redirectToAccount],
])("%s", (_name, build, path, redirect) => {
    it("constructs the URL from VITE_API_URL", () => {
        expect(build()).toBe(`http://api.test/api${path}`);
    });

    it("tolerates a trailing slash on VITE_API_URL", () => {
        vi.stubEnv("VITE_API_URL", "http://api.test/api/");
        expect(build()).toBe(`http://api.test/api${path}`);
    });

    it("returns null and warns when VITE_API_URL is missing", () => {
        vi.stubEnv("VITE_API_URL", "");
        const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
        expect(build()).toBeNull();
        expect(warn).toHaveBeenCalled();
    });

    it("navigates to the URL, and is a no-op without API config", () => {
        const assign = vi.fn();
        Object.defineProperty(window, "location", {
            writable: true,
            value: { ...window.location, assign },
        });
        redirect();
        expect(assign).toHaveBeenCalledWith(`http://api.test/api${path}`);

        assign.mockClear();
        vi.stubEnv("VITE_API_URL", "");
        vi.spyOn(console, "warn").mockImplementation(() => {});
        redirect();
        expect(assign).not.toHaveBeenCalled();
    });
});
