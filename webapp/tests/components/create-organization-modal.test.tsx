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

import CreateOrganizationModal from "@/components/create-organization-modal";
import { renderWithRouter } from "../test-utils";

beforeEach(() => {
    navigateMock.mockReset();
    createOrganizationMock.mockReset();
    createOrganizationMock.mockResolvedValue({
        id: "new-org",
        name: "Acme",
        description: "",
    });
});

describe("CreateOrganizationModal", () => {
    it("keeps the submit action disabled until a name is entered", async () => {
        renderWithRouter(
            <CreateOrganizationModal
                isOpen={true}
                onClose={vi.fn()}
                onOrganizationCreated={vi.fn().mockResolvedValue(undefined)}
            />,
        );

        const submit = screen.getByRole("button", {
            name: /^create organization$/i,
        });
        expect(submit).toBeDisabled();

        await userEvent.type(screen.getByLabelText(/^name$/i), "Acme");
        expect(submit).toBeEnabled();
    });

    it("submits name + description and navigates to the new organization", async () => {
        const onOrganizationCreated = vi.fn().mockResolvedValue(undefined);

        renderWithRouter(
            <CreateOrganizationModal
                isOpen={true}
                onClose={vi.fn()}
                onOrganizationCreated={onOrganizationCreated}
            />,
        );

        // The redesign labels the fields "Name" and "Description", and the
        // action "Create organization".
        await userEvent.type(screen.getByLabelText(/^name$/i), "Acme");
        await userEvent.type(
            screen.getByLabelText(/^description$/i),
            "Some desc",
        );

        await userEvent.click(
            screen.getByRole("button", { name: /^create organization$/i }),
        );

        // toast.promise resolves the inner thunk asynchronously.
        await vi.waitFor(() =>
            expect(createOrganizationMock).toHaveBeenCalledWith({
                name: "Acme",
                description: "Some desc",
            }),
        );
        await vi.waitFor(() =>
            expect(navigateMock).toHaveBeenCalledWith("/new-org"),
        );
        expect(onOrganizationCreated).toHaveBeenCalled();
    });
});
