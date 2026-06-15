import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const getProjectTokensMock = vi.hoisted(() => vi.fn());
const createProjectTokenMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/projectTokens", () => ({
    getProjectTokens: getProjectTokensMock,
    createProjectToken: createProjectTokenMock,
    deleteProjectToken: vi.fn(),
}));

import { ProjectTokensTable } from "@/components/projectTokens/projectTokenTable";
import { renderWithRouter } from "../../test-utils";

beforeEach(() => {
    getProjectTokensMock.mockReset();
    createProjectTokenMock.mockReset();
});

describe("ProjectTokensTable", () => {
    it("shows the empty-state copy when no tokens are returned", async () => {
        getProjectTokensMock.mockResolvedValue([]);
        renderWithRouter(<ProjectTokensTable projectId="p1" />);
        expect(
            await screen.findByText(/no api tokens found/i),
        ).toBeInTheDocument();
    });

    it("shows the create-token form when 'Create a new token' is clicked", async () => {
        getProjectTokensMock.mockResolvedValue([]);
        renderWithRouter(<ProjectTokensTable projectId="p1" />);
        await userEvent.click(
            await screen.findByRole("button", {
                name: /\+ create a new token/i,
            }),
        );
        expect(screen.getByPlaceholderText(/token name/i)).toBeInTheDocument();
    });

    it("renders existing tokens in the table", async () => {
        getProjectTokensMock.mockResolvedValue([
            {
                id: "t1",
                project_id: "p1",
                name: "ci-token",
                token: "tkn_xxx",
                access: 2,
                last_used: null,
            },
        ]);
        renderWithRouter(<ProjectTokensTable projectId="p1" />);
        expect(await screen.findByText("ci-token")).toBeInTheDocument();
        expect(screen.getByText("tkn_xxx")).toBeInTheDocument();
    });
});
