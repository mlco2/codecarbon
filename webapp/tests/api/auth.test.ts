import { describe, it, expect } from "vitest";
import { buildLoginUrl } from "@/api/auth";

describe("buildLoginUrl", () => {
    it("constructs login URL with redirect using URL constructor", () => {
        const url = new URL(buildLoginUrl());
        expect(url.origin + url.pathname).toBe(
            "http://api.test/api/auth/login",
        );
        expect(url.searchParams.get("redirect")).toBe(
            "http://app.test/home?auth=true",
        );
    });

    it("encodes redirect query parameter", () => {
        // The redirect value contains '?' and '=' which must be URL-encoded
        // when serialized. URL.searchParams handles this safely.
        const url = buildLoginUrl();
        expect(url).toContain(
            "redirect=http%3A%2F%2Fapp.test%2Fhome%3Fauth%3Dtrue",
        );
    });
});
