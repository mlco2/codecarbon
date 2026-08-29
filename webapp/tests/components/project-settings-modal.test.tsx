import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const updateProjectMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/projects", () => ({ updateProject: updateProjectMock }));

// The token table fetches on mount and is not what these tests are about.
vi.mock("@/components/projectTokens/projectTokenTable", () => ({
    ProjectTokensTable: () => <div data-testid="tokens" />,
}));

import ProjectSettingsModal from "@/components/project-settings-modal";

const project = {
    id: "p1",
    name: "Pipeline A",
    description: "Nightly training run",
    public: false,
    organizationId: "o1",
    experiments: [],
};

beforeEach(() => {
    updateProjectMock.mockReset();
    updateProjectMock.mockResolvedValue(project);
});

function renderModal(overrides: Record<string, unknown> = {}) {
    const onOpenChange = vi.fn();
    const onProjectUpdated = vi.fn();
    render(
        <ProjectSettingsModal
            open
            onOpenChange={onOpenChange}
            project={project}
            onProjectUpdated={onProjectUpdated}
            {...overrides}
        />,
    );
    return { onOpenChange, onProjectUpdated };
}

describe("ProjectSettingsModal", () => {
    it("saves the visibility toggle on its own and reveals the sharing link", async () => {
        renderModal();

        expect(
            screen.queryByRole("button", { name: /copy link/i }),
        ).not.toBeInTheDocument();

        await userEvent.click(
            screen.getByRole("switch", { name: /make project public/i }),
        );

        await waitFor(() =>
            expect(updateProjectMock).toHaveBeenCalledWith("p1", {
                name: project.name,
                description: project.description,
                public: true,
            }),
        );
        expect(
            await screen.findByRole("button", { name: /copy link/i }),
        ).toBeInTheDocument();
    });

    it("does not commit unsaved field edits when the toggle is flipped", async () => {
        renderModal();

        const name = screen.getByLabelText(/^name$/i);
        await userEvent.clear(name);
        await userEvent.type(name, "Renamed but unsaved");

        await userEvent.click(
            screen.getByRole("switch", { name: /make project public/i }),
        );

        await waitFor(() =>
            expect(updateProjectMock).toHaveBeenCalledWith(
                "p1",
                expect.objectContaining({ name: project.name }),
            ),
        );
    });

    it("rolls the toggle back when the write fails", async () => {
        updateProjectMock.mockRejectedValue(new Error("nope"));
        vi.spyOn(console, "error").mockImplementation(() => {});
        renderModal();

        const toggle = screen.getByRole("switch", {
            name: /make project public/i,
        });
        await userEvent.click(toggle);

        await waitFor(() =>
            expect(toggle).toHaveAttribute("data-state", "unchecked"),
        );
        expect(
            screen.queryByRole("button", { name: /copy link/i }),
        ).not.toBeInTheDocument();
    });

    it("closes on a successful save", async () => {
        const { onOpenChange, onProjectUpdated } = renderModal();

        await userEvent.click(
            screen.getByRole("button", { name: /save changes/i }),
        );

        await waitFor(() => expect(onProjectUpdated).toHaveBeenCalled());
        expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it("stays open when the save fails, so the edits survive", async () => {
        updateProjectMock.mockRejectedValue(new Error("nope"));
        vi.spyOn(console, "error").mockImplementation(() => {});
        const { onOpenChange } = renderModal();

        await userEvent.click(
            screen.getByRole("button", { name: /save changes/i }),
        );

        await waitFor(() => expect(updateProjectMock).toHaveBeenCalled());
        expect(onOpenChange).not.toHaveBeenCalledWith(false);
    });

    it("opens on General, whichever tab it was left on", async () => {
        const { rerender } = render(
            <ProjectSettingsModal
                open
                onOpenChange={vi.fn()}
                project={project}
                onProjectUpdated={vi.fn()}
            />,
        );

        await userEvent.click(screen.getByRole("tab", { name: /api tokens/i }));
        expect(
            screen.getByRole("tab", { name: /api tokens/i }),
        ).toHaveAttribute("aria-selected", "true");

        // Closed and opened again: the dialog stays mounted between openings.
        rerender(
            <ProjectSettingsModal
                open={false}
                onOpenChange={vi.fn()}
                project={project}
                onProjectUpdated={vi.fn()}
            />,
        );
        rerender(
            <ProjectSettingsModal
                open
                onOpenChange={vi.fn()}
                project={project}
                onProjectUpdated={vi.fn()}
            />,
        );

        expect(screen.getByRole("tab", { name: /general/i })).toHaveAttribute(
            "aria-selected",
            "true",
        );
    });

    it("disables the save action until the project has a name", async () => {
        renderModal();

        const save = screen.getByRole("button", { name: /save changes/i });
        expect(save).toBeEnabled();

        await userEvent.clear(screen.getByLabelText(/^name$/i));
        expect(save).toBeDisabled();
    });
});
