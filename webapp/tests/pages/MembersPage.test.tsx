import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
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

const addOrganizationUserMock = vi.hoisted(() => vi.fn());
const removeUserFromOrganizationMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/organizations", () => ({
    addOrganizationUser: addOrganizationUserMock,
    removeUserFromOrganization: removeUserFromOrganizationMock,
}));

import MembersPage from "@/pages/MembersPage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

beforeEach(() => {
    fetcherMock.mockReset();
    addOrganizationUserMock.mockReset();
    addOrganizationUserMock.mockResolvedValue(undefined);
    removeUserFromOrganizationMock.mockReset();
    removeUserFromOrganizationMock.mockResolvedValue(undefined);
});

/* The viewer, and the members the list comes back with. `/auth/check` decides
   who is looking; their own row in the list decides whether they administer
   this organization. */
function mockMembers(members: unknown[], viewerId: string | null = null) {
    fetcherMock.mockImplementation((url: string) => {
        if (url.endsWith("/users")) return Promise.resolve(members);
        if (url === "/auth/check")
            return Promise.resolve(viewerId ? { user: { id: viewerId } } : {});
        return mockOrganization(url) ?? Promise.resolve(null);
    });
}

const ADMIN = {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    organization_id: "o1",
    is_admin: true,
};

const MEMBER = {
    id: "u2",
    name: "Bob",
    email: "bob@example.com",
    organization_id: "o1",
    is_admin: false,
};

function mockOrganization(url: string) {
    if (url.endsWith("/organizations/o1")) {
        return Promise.resolve({ id: "o1", name: "Acme", description: "" });
    }
    return undefined;
}

function renderWithSwr(node: React.ReactNode) {
    return renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            {node}
        </SWRConfig>,
    );
}

describe("MembersPage", () => {
    it("renders the member list once loaded", async () => {
        // SWR calls the fetcher per key; first matching response wins per key.
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) {
                return Promise.resolve([
                    {
                        id: "u1",
                        name: "Alice",
                        email: "alice@example.com",
                        organization_id: "o1",
                        is_admin: true,
                    },
                ]);
            }
            return mockOrganization(url) ?? Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        expect(await screen.findByText("Alice")).toBeInTheDocument();
        expect(screen.getByText("alice@example.com")).toBeInTheDocument();
        // The status slot carries the only standing the API records.
        expect(screen.getByText("(Admin)")).toBeInTheDocument();
    });

    it("shows the empty state when the organization has no members", async () => {
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) return Promise.resolve([]);
            return mockOrganization(url) ?? Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        expect(
            await screen.findByText(/you have no members invited yet/i),
        ).toBeInTheDocument();
    });

    it("keeps the invite button disabled until an address is typed", async () => {
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) return Promise.resolve([]);
            return mockOrganization(url) ?? Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        const button = await screen.findByRole("button", { name: /invite/i });
        expect(button).toBeDisabled();

        await userEvent.type(
            screen.getByLabelText(/invite via email/i),
            "new@example.com",
        );
        expect(button).toBeEnabled();
    });

    it("invites the typed address", async () => {
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) return Promise.resolve([]);
            return mockOrganization(url) ?? Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        await userEvent.type(
            await screen.findByLabelText(/invite via email/i),
            "new@example.com",
        );
        await userEvent.click(screen.getByRole("button", { name: /invite/i }));

        expect(addOrganizationUserMock).toHaveBeenCalledWith(
            "o1",
            "new@example.com",
        );
    });

    it("does not send an invalid address to the API", async () => {
        fetcherMock.mockImplementation((url: string) => {
            if (url.endsWith("/users")) return Promise.resolve([]);
            return mockOrganization(url) ?? Promise.resolve(null);
        });

        renderWithSwr(<MembersPage />);

        await userEvent.type(
            await screen.findByLabelText(/invite via email/i),
            "not-an-email",
        );
        await userEvent.click(screen.getByRole("button", { name: /invite/i }));

        // `type="email"` fails the form's own constraint validation, so the
        // submit never reaches the handler. The page's schema check behind it
        // covers whatever the browser lets through.
        expect(addOrganizationUserMock).not.toHaveBeenCalled();
    });

    it("offers no actions to a member who is not an admin", async () => {
        mockMembers([ADMIN, MEMBER], MEMBER.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        expect(
            screen.queryByRole("button", { name: /actions for/i }),
        ).not.toBeInTheDocument();
    });

    it("lets an admin remove any member, administrators included", async () => {
        mockMembers([ADMIN, MEMBER], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        // The API refuses only the last administrator, so both rows have a menu.
        expect(
            screen.getByRole("button", { name: /actions for Alice/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /actions for Bob/i }),
        ).toBeInTheDocument();
    });

    it("removes the member only once the dialog is confirmed", async () => {
        mockMembers([ADMIN, MEMBER], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        await userEvent.click(
            screen.getByRole("button", { name: /actions for Bob/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Delete" }),
        );

        // The menu item opens the dialog; nothing has been sent yet.
        expect(removeUserFromOrganizationMock).not.toHaveBeenCalled();

        await userEvent.click(
            await screen.findByRole("button", { name: /remove member/i }),
        );
        expect(removeUserFromOrganizationMock).toHaveBeenCalledWith("o1", "u2");
    });

    it("offers no Settings action, which has no endpoint behind it", async () => {
        mockMembers([ADMIN, MEMBER], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        await userEvent.click(
            screen.getByRole("button", { name: /actions for Bob/i }),
        );

        await screen.findByRole("menuitem", { name: "Delete" });
        expect(
            screen.queryByRole("menuitem", { name: /settings/i }),
        ).not.toBeInTheDocument();
    });

    it("names the member and the organization in the confirmation", async () => {
        mockMembers([ADMIN, MEMBER], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        await userEvent.click(
            screen.getByRole("button", { name: /actions for Bob/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Delete" }),
        );

        expect(
            await screen.findByText(/Remove Bob from Acme\?/),
        ).toBeInTheDocument();
    });

    it("does not remove a member when the confirmation is cancelled", async () => {
        mockMembers([ADMIN, MEMBER], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Bob");
        await userEvent.click(
            screen.getByRole("button", { name: /actions for Bob/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Delete" }),
        );
        await userEvent.click(
            await screen.findByRole("button", { name: /cancel/i }),
        );

        expect(removeUserFromOrganizationMock).not.toHaveBeenCalled();
    });

    it("keeps the dialog open when the API refuses the removal", async () => {
        removeUserFromOrganizationMock.mockRejectedValue(
            new Error(
                "Cannot remove the last administrator of the organization",
            ),
        );
        mockMembers([ADMIN], ADMIN.id);

        renderWithSwr(<MembersPage />);

        await screen.findByText("Alice");
        await userEvent.click(
            screen.getByRole("button", { name: /actions for Alice/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Delete" }),
        );
        await userEvent.click(
            await screen.findByRole("button", { name: /remove member/i }),
        );

        await waitFor(() =>
            expect(removeUserFromOrganizationMock).toHaveBeenCalledWith(
                "o1",
                "u1",
            ),
        );
        expect(
            await screen.findByRole("button", { name: /cancel/i }),
        ).toBeInTheDocument();
    });
});
