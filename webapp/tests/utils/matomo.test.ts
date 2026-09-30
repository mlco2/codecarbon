import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { initMatomo, trackEvent } from "@/utils/matomo";

function fakeRouter(pathname: string) {
    let listener: ((s: { location: { pathname: string } }) => void) | null =
        null;
    return {
        state: { location: { pathname } },
        subscribe(fn: typeof listener) {
            listener = fn;
            return () => {};
        },
        navigate(next: string) {
            listener?.({ location: { pathname: next } });
        },
    };
}

beforeEach(() => {
    window._paq = undefined;
    document.head.innerHTML = "";
});

afterEach(() => {
    vi.unstubAllEnvs();
});

describe("initMatomo", () => {
    it("does nothing when Matomo is not configured", () => {
        const router = fakeRouter("/home");
        initMatomo(router);
        expect(window._paq).toBeUndefined();
        expect(document.head.querySelector("script")).toBeNull();
    });

    it("tracks the first page and each new pathname once", () => {
        vi.stubEnv("VITE_MATOMO_URL", "https://matomo.example.com");
        vi.stubEnv("VITE_MATOMO_SITE_ID", "3");
        const router = fakeRouter("/home");

        initMatomo(router);
        router.navigate("/home");
        router.navigate("/organizations/1");

        const views = window._paq!.filter((c) => c[0] === "trackPageView");
        expect(views).toHaveLength(2);
        expect(window._paq).toContainEqual(["setSiteId", "3"]);
        expect(window._paq).toContainEqual([
            "setTrackerUrl",
            "https://matomo.example.com/matomo.php",
        ]);
        expect(window._paq).toContainEqual([
            "setCustomUrl",
            `${window.location.origin}/organizations/1`,
        ]);
        expect(document.head.querySelector("script")?.src).toBe(
            "https://matomo.example.com/matomo.js",
        );
    });

    it("records events with an optional name and value once enabled", () => {
        vi.stubEnv("VITE_MATOMO_URL", "https://matomo.example.com");
        vi.stubEnv("VITE_MATOMO_SITE_ID", "3");
        initMatomo(fakeRouter("/home"));

        trackEvent("Activation", "project_created");
        trackEvent("Dashboard", "date_range_applied", undefined, 30);
        trackEvent("Dashboard", "chart_viewed", "Emissions", 12);

        expect(window._paq).toContainEqual([
            "trackEvent",
            "Activation",
            "project_created",
        ]);
        expect(window._paq).toContainEqual([
            "trackEvent",
            "Dashboard",
            "date_range_applied",
            "",
            30,
        ]);
        expect(window._paq).toContainEqual([
            "trackEvent",
            "Dashboard",
            "chart_viewed",
            "Emissions",
            12,
        ]);
    });
});
