import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigateMock = vi.hoisted(() => vi.fn());
vi.mock("react-router-dom", async () => {
    const actual =
        await vi.importActual<typeof import("react-router-dom")>(
            "react-router-dom",
        );
    return { ...actual, useNavigate: () => navigateMock };
});

const fetcherMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/swr", () => ({ fetcher: fetcherMock, swrConfig: {} }));

import SettingsPage from "@/pages/SettingsPage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

function renderPage() {
    return renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            <SettingsPage />
        </SWRConfig>,
    );
}

beforeEach(() => {
    fetcherMock.mockReset();
    navigateMock.mockReset();
    fetcherMock.mockResolvedValue({ user: { email: "person@example.com" } });
});

describe("SettingsPage", () => {
    it("shows the signed-in address rather than a placeholder", async () => {
        renderPage();
        expect(
            await screen.findByDisplayValue("person@example.com"),
        ).toBeDisabled();
    });

    it("marks Profile as the panel being viewed, and does not make it pressable", () => {
        renderPage();
        // The current row is not a button: there is nothing to press.
        expect(
            screen.queryByRole("button", { name: /profile/i }),
        ).not.toBeInTheDocument();
        expect(
            screen.getByText("Profile", { selector: "span" }),
        ).toBeInTheDocument();
    });

    it("goes back through history", async () => {
        renderPage();
        await userEvent.click(screen.getByRole("button", { name: /go back/i }));
        expect(navigateMock).toHaveBeenCalledWith(-1);
    });

    it("disables the provider hand-offs when no provider is configured", () => {
        renderPage();
        // VITE_OIDC_PROFILE_URL is unset in tests, so both are inert.
        expect(
            screen.getByRole("button", { name: /password/i }),
        ).toBeDisabled();
        expect(screen.getByRole("button", { name: /change/i })).toBeDisabled();
    });
});
