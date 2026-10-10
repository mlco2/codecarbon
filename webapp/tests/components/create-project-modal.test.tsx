import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createProjectMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/projects", () => ({
    createProject: createProjectMock,
}));

import CreateProjectModal from "@/components/create-project-modal";

beforeEach(() => {
    createProjectMock.mockReset();
    createProjectMock.mockResolvedValue({
        id: "p1",
        name: "Created",
        description: "",
        public: false,
        organizationId: "o1",
        experiments: [],
    });
});

describe("CreateProjectModal", () => {
    it("keeps the submit action disabled until a name is entered", async () => {
        render(
            <CreateProjectModal
                organizationId="o1"
                isOpen={true}
                onClose={vi.fn()}
                onProjectCreated={vi.fn().mockResolvedValue(undefined)}
            />,
        );

        const submit = screen.getByRole("button", {
            name: /^create project$/i,
        });
        expect(submit).toBeDisabled();

        await userEvent.type(screen.getByLabelText(/^name$/i), "New project");
        expect(submit).toBeEnabled();
    });

    it("submits the form with name + description and the parent org id", async () => {
        const onProjectCreated = vi.fn().mockResolvedValue(undefined);
        const onClose = vi.fn();

        render(
            <CreateProjectModal
                organizationId="o1"
                isOpen={true}
                onClose={onClose}
                onProjectCreated={onProjectCreated}
            />,
        );

        // The redesign labels the fields "Name" and "Description", and the
        // action "Create project".
        await userEvent.type(screen.getByLabelText(/^name$/i), "New project");
        await userEvent.type(
            screen.getByLabelText(/^description$/i),
            "Some desc",
        );

        await userEvent.click(
            screen.getByRole("button", { name: /^create project$/i }),
        );

        // toast.promise resolves the inner thunk asynchronously.
        await vi.waitFor(() =>
            expect(createProjectMock).toHaveBeenCalledWith("o1", {
                name: "New project",
                description: "Some desc",
            }),
        );
    });
});
