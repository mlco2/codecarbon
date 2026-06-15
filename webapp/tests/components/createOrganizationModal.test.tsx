import { describe, it, expect, vi, beforeEach } from "vitest";
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

const createOrganizationMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/organizations", () => ({
    createOrganization: createOrganizationMock,
}));

const toastErrorMock = vi.hoisted(() => vi.fn());
vi.mock("sonner", () => ({
    toast: {
        promise: vi.fn((p) => ({ unwrap: () => p })),
        error: toastErrorMock,
        success: vi.fn(),
    },
}));

import CreateOrganizationModal from "@/components/createOrganizationModal";
import { renderWithRouter } from "../test-utils";

beforeEach(() => {
    navigateMock.mockReset();
    createOrganizationMock.mockReset();
    toastErrorMock.mockReset();
});

describe("CreateOrganizationModal", () => {
    it("rejects an empty name with a toast error", async () => {
        const onClose = vi.fn();
        const onOrganizationCreated = vi.fn().mockResolvedValue(undefined);

        renderWithRouter(
            <CreateOrganizationModal
                isOpen={true}
                onClose={onClose}
                onOrganizationCreated={onOrganizationCreated}
            />,
        );

        await userEvent.click(
            screen.getByRole("button", { name: /^create$/i }),
        );

        expect(toastErrorMock).toHaveBeenCalledWith(
            "Organization name is required",
        );
        expect(createOrganizationMock).not.toHaveBeenCalled();
    });

    it("creates an organization and navigates to its dashboard", async () => {
        createOrganizationMock.mockResolvedValue({
            id: "new-org",
            name: "Acme",
            description: "",
        });
        const onOrganizationCreated = vi.fn().mockResolvedValue(undefined);

        renderWithRouter(
            <CreateOrganizationModal
                isOpen={true}
                onClose={() => {}}
                onOrganizationCreated={onOrganizationCreated}
            />,
        );

        await userEvent.type(
            screen.getByPlaceholderText(/organization name/i),
            "Acme",
        );
        await userEvent.click(
            screen.getByRole("button", { name: /^create$/i }),
        );

        await vi.waitFor(() =>
            expect(navigateMock).toHaveBeenCalledWith("/new-org"),
        );
    });
});
