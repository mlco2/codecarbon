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
vi.mock("@/api/organizations", () => ({ getOrganizations: vi.fn() }));

import OrganizationsMenu from "@/components/organizations-menu";
import { renderWithRouter } from "../test-utils";
import { SWRConfig } from "swr";

const orgs = [
    { id: "o1", name: "Mozilla", description: "", is_admin: true },
    { id: "o2", name: "Wecasa", description: "", is_admin: false },
];

/* `o1` is administered by the signed-in user and `o2` is not, which is the split
   the menu draws: administered dashboards below the rule, invited ones above it. */
function mockApi() {
    fetcherMock.mockImplementation(() => Promise.resolve([]));
}

function renderMenu() {
    const onSelectOrg = vi.fn();
    renderWithRouter(
        <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
            <OrganizationsMenu
                orgs={orgs}
                selectedOrg="o1"
                onSelectOrg={onSelectOrg}
            >
                <button type="button">Organizations</button>
            </OrganizationsMenu>
        </SWRConfig>,
    );
    return { onSelectOrg };
}

beforeEach(() => {
    fetcherMock.mockReset();
    navigateMock.mockReset();
    mockApi();
});

describe("OrganizationsMenu", () => {
    it("lists the dashboards once opened", async () => {
        renderMenu();
        await userEvent.click(
            screen.getByRole("button", { name: "Organizations" }),
        );

        expect(
            await screen.findByRole("menuitem", { name: "Mozilla" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("menuitem", { name: "Wecasa" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("menuitem", { name: /add new organization/i }),
        ).toBeInTheDocument();
    });

    it("marks the dashboard being viewed", async () => {
        renderMenu();
        await userEvent.click(
            screen.getByRole("button", { name: "Organizations" }),
        );

        expect(
            await screen.findByRole("menuitem", { name: "Mozilla" }),
        ).toHaveAttribute("aria-current", "true");
        expect(
            screen.getByRole("menuitem", { name: "Wecasa" }),
        ).not.toHaveAttribute("aria-current");
    });

    it("separates administered dashboards from invited ones", async () => {
        renderMenu();
        await userEvent.click(
            screen.getByRole("button", { name: "Organizations" }),
        );

        // The heading only appears when there is something invited to list.
        expect(
            await screen.findByText(/dashboards you've been invited to/i),
        ).toBeInTheDocument();

        const items = screen
            .getAllByRole("menuitem")
            .map((item) => item.textContent);
        // Invited first, administered after the rule.
        expect(items.indexOf("Wecasa")).toBeLessThan(items.indexOf("Mozilla"));
    });

    it("keeps that split after the menu is closed and reopened", async () => {
        renderMenu();
        const trigger = screen.getByRole("button", { name: "Organizations" });

        await userEvent.click(trigger);
        await screen.findByText(/dashboards you've been invited to/i);
        await userEvent.keyboard("{Escape}");
        await userEvent.click(trigger);

        // Regression: an admin lookup keyed on `open` dropped its result here,
        // and every dashboard fell back into the invited group.
        const items = screen
            .getAllByRole("menuitem")
            .map((item) => item.textContent);
        expect(items.indexOf("Wecasa")).toBeLessThan(items.indexOf("Mozilla"));
    });

    it("reads admin rights from the list, not one request per organization", async () => {
        renderMenu();
        await userEvent.click(
            screen.getByRole("button", { name: "Organizations" }),
        );
        await screen.findByText(/dashboards you've been invited to/i);

        expect(fetcherMock).not.toHaveBeenCalled();
    });

    it("switches dashboard when one is picked", async () => {
        const { onSelectOrg } = renderMenu();
        await userEvent.click(
            screen.getByRole("button", { name: "Organizations" }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Wecasa" }),
        );
        expect(onSelectOrg).toHaveBeenCalledWith("o2");
    });
});
