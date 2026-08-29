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

const addOrganizationUserMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/organizations", () => ({
    addOrganizationUser: addOrganizationUserMock,
}));

import MembersPage from "@/pages/MembersPage";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

beforeEach(() => {
    fetcherMock.mockReset();
    addOrganizationUserMock.mockReset();
    addOrganizationUserMock.mockResolvedValue(undefined);
});

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
});
