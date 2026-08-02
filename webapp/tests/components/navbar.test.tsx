import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigateMock = vi.hoisted(() => vi.fn());
vi.mock("react-router-dom", async () => {
    const actual =
        await vi.importActual<typeof import("react-router-dom")>(
            "react-router-dom",
        );
    return {
        ...actual,
        useNavigate: () => navigateMock,
        useLocation: () => ({ pathname: "/o1" }),
    };
});

vi.mock("@/api/organizations", () => ({
    getOrganizations: vi.fn().mockResolvedValue([]),
}));

import NavBar from "@/components/navbar";
import { renderWithRouter } from "../test-utils";

beforeEach(() => {
    navigateMock.mockReset();
    localStorage.clear();
});

const orgs = [
    { id: "o1", name: "Acme", description: "" },
    { id: "o2", name: "Beta", description: "" },
];

describe("NavBar", () => {
    it("renders the primary nav items", () => {
        renderWithRouter(<NavBar orgs={orgs} />);
        expect(
            screen.getByRole("button", { name: /home/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /projects/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /members/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /log out/i }),
        ).toBeInTheDocument();
    });

    it("navigates to the organization root when Home is clicked", async () => {
        renderWithRouter(<NavBar orgs={orgs} />);
        await userEvent.click(screen.getByRole("button", { name: /home/i }));
        expect(navigateMock).toHaveBeenCalledWith("/o1");
    });

    it("navigates to /<org>/projects when Projects is clicked", async () => {
        renderWithRouter(<NavBar orgs={orgs} />);
        await userEvent.click(
            screen.getByRole("button", { name: /projects/i }),
        );
        expect(navigateMock).toHaveBeenCalledWith("/o1/projects");
    });
});
