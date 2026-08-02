import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";

vi.mock("react-router-dom", async () => {
    const actual =
        await vi.importActual<typeof import("react-router-dom")>(
            "react-router-dom",
        );
    return { ...actual, useParams: () => ({ organizationId: "o1" }) };
});

const fetcherMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/swr", () => ({
    fetcher: fetcherMock,
    swrConfig: {},
}));

vi.mock("@/api/projects", () => ({
    getProjects: vi.fn().mockResolvedValue([]),
    deleteProject: vi.fn(),
}));

import ProjectsPage from "@/pages/ProjectsPage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

beforeEach(() => {
    fetcherMock.mockReset();
});

function renderWithSwr(node: React.ReactNode) {
    return renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            {node}
        </SWRConfig>,
    );
}

describe("ProjectsPage", () => {
    it("lists projects once SWR resolves", async () => {
        // SWR fetcher returns the wire shape — snake_case organization_id.
        fetcherMock.mockResolvedValue([
            {
                id: "p1",
                name: "Pipeline A",
                description: "First pipeline",
                public: false,
                organization_id: "o1",
                experiments: [],
            },
            {
                id: "p2",
                name: "Pipeline B",
                description: "Second pipeline",
                public: true,
                organization_id: "o1",
                experiments: [],
            },
        ]);

        renderWithSwr(<ProjectsPage />);

        await waitFor(() =>
            expect(screen.getByText("Pipeline A")).toBeInTheDocument(),
        );
        expect(screen.getByText("Pipeline B")).toBeInTheDocument();
    });

    it("renders the empty table when there are no projects", async () => {
        fetcherMock.mockResolvedValue([]);
        renderWithSwr(<ProjectsPage />);
        expect(
            await screen.findByRole("heading", { name: /projects/i }),
        ).toBeInTheDocument();
        expect(screen.queryByText("Pipeline A")).not.toBeInTheDocument();
    });
});
