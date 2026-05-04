import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

const redirectMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/auth", () => ({
    redirectToLogin: redirectMock,
    buildLoginUrl: () => "http://api.test/api/auth/login?redirect=...",
}));

const isMockModeMock = vi.hoisted(() => vi.fn(() => false));
vi.mock("@/api/mock", () => ({
    isMockMode: isMockModeMock,
}));

import AuthGuard from "./auth-guard";

const originalFetch = globalThis.fetch;

beforeEach(() => {
    redirectMock.mockReset();
    isMockModeMock.mockReturnValue(false);
});

afterEach(() => {
    globalThis.fetch = originalFetch;
});

describe("AuthGuard", () => {
    it("renders children when /auth/check returns a user", async () => {
        globalThis.fetch = vi.fn(async () => ({
            ok: true,
            json: async () => ({ user: { id: "u1" } }),
        })) as unknown as typeof fetch;

        render(
            <AuthGuard>
                <div>secret content</div>
            </AuthGuard>,
        );

        await waitFor(() =>
            expect(screen.getByText("secret content")).toBeInTheDocument(),
        );
        expect(redirectMock).not.toHaveBeenCalled();
    });

    it("redirects to login when /auth/check returns no user", async () => {
        globalThis.fetch = vi.fn(async () => ({
            ok: true,
            json: async () => ({ user: null }),
        })) as unknown as typeof fetch;

        render(
            <AuthGuard>
                <div>secret content</div>
            </AuthGuard>,
        );

        await waitFor(() => expect(redirectMock).toHaveBeenCalledOnce());
        expect(screen.queryByText("secret content")).not.toBeInTheDocument();
    });

    it("redirects to login when /auth/check fetch throws", async () => {
        globalThis.fetch = vi.fn(async () => {
            throw new Error("network");
        }) as unknown as typeof fetch;

        render(
            <AuthGuard>
                <div>secret content</div>
            </AuthGuard>,
        );

        await waitFor(() => expect(redirectMock).toHaveBeenCalledOnce());
    });

    it("renders children immediately in mock mode without calling fetch", () => {
        isMockModeMock.mockReturnValue(true);
        const fetchSpy = vi.fn();
        globalThis.fetch = fetchSpy as unknown as typeof fetch;

        render(
            <AuthGuard>
                <div>secret content</div>
            </AuthGuard>,
        );

        expect(screen.getByText("secret content")).toBeInTheDocument();
        expect(fetchSpy).not.toHaveBeenCalled();
        expect(redirectMock).not.toHaveBeenCalled();
    });
});
