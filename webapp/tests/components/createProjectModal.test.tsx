import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createProjectMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/projects", () => ({
    createProject: createProjectMock,
}));

import CreateProjectModal from "@/components/createProjectModal";

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

        await userEvent.type(
            screen.getByPlaceholderText(/project name/i),
            "New project",
        );
        await userEvent.type(
            screen.getByPlaceholderText(/project description/i),
            "Some desc",
        );

        await userEvent.click(
            screen.getByRole("button", { name: /^create$/i }),
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
