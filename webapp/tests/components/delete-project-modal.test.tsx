import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DeleteProjectModal from "@/components/delete-project-modal";

beforeEach(() => {
    vi.restoreAllMocks();
});

describe("DeleteProjectModal", () => {
    it("disables the destructive action until the project name is typed exactly", async () => {
        const onDelete = vi.fn().mockResolvedValue(undefined);
        render(
            <DeleteProjectModal
                open={true}
                onOpenChange={() => {}}
                projectName="my-project"
                projectId="p1"
                onDelete={onDelete}
            />,
        );

        const button = screen.getByRole("button", { name: /delete project/i });
        expect(button).toBeDisabled();

        const input = screen.getByPlaceholderText("my-project");
        await userEvent.type(input, "my-project");
        expect(button).toBeEnabled();

        await userEvent.click(button);
        expect(onDelete).toHaveBeenCalledWith("p1");
    });

    it("does not call onDelete when confirmation does not match", async () => {
        const onDelete = vi.fn();
        render(
            <DeleteProjectModal
                open={true}
                onOpenChange={() => {}}
                projectName="my-project"
                projectId="p1"
                onDelete={onDelete}
            />,
        );
        const input = screen.getByPlaceholderText("my-project");
        await userEvent.type(input, "wrong");
        const button = screen.getByRole("button", { name: /delete project/i });
        expect(button).toBeDisabled();
        // Force-click to verify the handler still bails out
        await userEvent.click(button);
        expect(onDelete).not.toHaveBeenCalled();
    });
});
