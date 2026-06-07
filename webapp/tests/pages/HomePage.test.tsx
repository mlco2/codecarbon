import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";

const navigateMock = vi.hoisted(() => vi.fn());
vi.mock("react-router-dom", async () => {
    const actual =
        await vi.importActual<typeof import("react-router-dom")>(
            "react-router-dom",
        );
    return { ...actual, useNavigate: () => navigateMock };
});

const fetcherMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/swr", () => ({
    fetcher: fetcherMock,
    swrConfig: {},
}));

import HomePage from "@/pages/HomePage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

beforeEach(() => {
    navigateMock.mockReset();
    fetcherMock.mockReset();
    localStorage.clear();
});

function renderWithSwr(node: React.ReactNode) {
    return renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            {node}
        </SWRConfig>,
    );
}

describe("HomePage", () => {
    it("redirects to the first organization once it loads", async () => {
        fetcherMock.mockResolvedValue([
            { id: "org-99", name: "Acme", description: "" },
        ]);

        renderWithSwr(<HomePage />);

        await waitFor(() =>
            expect(navigateMock).toHaveBeenCalledWith("/org-99"),
        );
        expect(localStorage.getItem("organizationId")).toBe("org-99");
        expect(localStorage.getItem("organizationName")).toBe("Acme");
    });

    it("shows the get-started card when the user has no organizations", async () => {
        fetcherMock.mockResolvedValue([]);
        renderWithSwr(<HomePage />);

        expect(
            await screen.findByRole("heading", { name: /get started/i }),
        ).toBeInTheDocument();
        expect(navigateMock).not.toHaveBeenCalled();
    });
});
