import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigateMock = vi.hoisted(() => vi.fn());
const locationMock = vi.hoisted(() => ({ current: { pathname: "/o1" } }));
vi.mock("react-router-dom", async () => {
    const actual =
        await vi.importActual<typeof import("react-router-dom")>(
            "react-router-dom",
        );
    return {
        ...actual,
        useNavigate: () => navigateMock,
        useLocation: () => locationMock.current,
    };
});

// The account menu fetches on open; the rail's own behaviour is what is tested.
vi.mock("@/components/account-menu", () => ({
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import SidebarRail from "@/components/sidebar-rail";
import { renderWithRouter } from "../test-utils";

const orgs = [
    { id: "o1", name: "Mozilla", description: "" },
    { id: "o2", name: "Wecasa", description: "" },
];

beforeEach(() => {
    navigateMock.mockReset();
    localStorage.clear();
    locationMock.current = { pathname: "/o1" };
});

describe("SidebarRail", () => {
    it("offers the dashboard's destinations", () => {
        renderWithRouter(<SidebarRail orgs={orgs} />);
        ["Global", "Projects", "Members", "Account"].forEach((label) =>
            expect(
                screen.getByRole("button", { name: label }),
            ).toBeInTheDocument(),
        );
    });

    it("marks the destination matching the current path", () => {
        locationMock.current = { pathname: "/o1/projects" };
        renderWithRouter(<SidebarRail orgs={orgs} />);

        expect(
            screen.getByRole("button", { name: "Projects" }),
        ).toHaveAttribute("aria-current", "page");
        expect(
            screen.getByRole("button", { name: "Global" }),
        ).not.toHaveAttribute("aria-current");
    });

    it("navigates within the organization in the URL", async () => {
        locationMock.current = { pathname: "/o2/members" };
        renderWithRouter(<SidebarRail orgs={orgs} />);

        await userEvent.click(screen.getByRole("button", { name: "Projects" }));
        expect(navigateMock).toHaveBeenCalledWith("/o2/projects");
    });

    it("remembers the organization it resolved, for the pages that read it", () => {
        renderWithRouter(<SidebarRail orgs={orgs} />);
        expect(localStorage.getItem("organizationId")).toBe("o1");
        expect(localStorage.getItem("organizationName")).toBe("Mozilla");
    });

    it("does not navigate before an organization is known", async () => {
        renderWithRouter(<SidebarRail orgs={[]} />);
        await userEvent.click(screen.getByRole("button", { name: "Projects" }));
        expect(navigateMock).not.toHaveBeenCalled();
    });
});
