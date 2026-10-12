import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

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

const removeUserMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/organizations", () => ({
    removeUserFromOrganization: removeUserMock,
}));

import MembersPage from "@/pages/MembersPage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

beforeEach(() => {
    fetcherMock.mockReset();
    removeUserMock.mockReset();
    removeUserMock.mockResolvedValue(undefined);
});

function mockOrgWithMember() {
    fetcherMock.mockImplementation((url: string) => {
        if (url.endsWith("/users")) {
            return Promise.resolve([
                {
                    id: "u1",
                    name: "Alice",
                    email: "alice@example.com",
                    is_active: true,
                    organizations: ["o1"],
                },
            ]);
        }
        if (url.endsWith("/organizations/o1")) {
            return Promise.resolve({ id: "o1", name: "Acme", description: "" });
        }
        return Promise.resolve(null);
    });
}

function renderWithSwr(node: React.ReactNode) {
    return renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            {node}
        </SWRConfig>,
    );
}

describe("MembersPage", () => {
    it("renders the user list once loaded", async () => {
        // SWR calls the fetcher per key; first matching response wins per key.
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) {
                return Promise.resolve([
                    {
                        id: "u1",
                        name: "Alice",
                        email: "alice@example.com",
                        is_active: true,
                        organizations: ["o1"],
                    },
                ]);
            }
            if (url.endsWith("/organizations/o1")) {
                return Promise.resolve({
                    id: "o1",
                    name: "Acme",
                    description: "",
                });
            }
            return Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        expect(await screen.findByText("Alice")).toBeInTheDocument();
        expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    });

    it("opens the add-member form when the button is clicked", async () => {
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) return Promise.resolve([]);
            if (url.endsWith("/organizations/o1"))
                return Promise.resolve({
                    id: "o1",
                    name: "Acme",
                    description: "",
                });
            return Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);
        await userEvent.click(
            await screen.findByRole("button", { name: /\+ add a member/i }),
        );
        expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    });

    it("removes a member through the row menu once confirmed", async () => {
        mockOrgWithMember();
        renderWithSwr(<MembersPage />);

        expect(await screen.findByText("Alice")).toBeInTheDocument();
        await userEvent.click(screen.getByRole("button", { name: /toggle/i }));
        await userEvent.click(
            await screen.findByRole("menuitem", { name: /delete/i }),
        );

        await userEvent.click(
            await screen.findByRole("button", { name: /remove member/i }),
        );
        expect(removeUserMock).toHaveBeenCalledWith("o1", "u1");
    });

    it("does not remove a member when the confirmation is cancelled", async () => {
        mockOrgWithMember();
        renderWithSwr(<MembersPage />);

        expect(await screen.findByText("Alice")).toBeInTheDocument();
        await userEvent.click(screen.getByRole("button", { name: /toggle/i }));
        await userEvent.click(
            await screen.findByRole("menuitem", { name: /delete/i }),
        );
        await userEvent.click(
            await screen.findByRole("button", { name: /cancel/i }),
        );
        expect(removeUserMock).not.toHaveBeenCalled();
    });
});
