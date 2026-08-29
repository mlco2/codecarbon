import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ProjectRow from "@/components/project-row";
import { Table, TableBody } from "@/components/ui/table";
import { renderWithRouter } from "../test-utils";

const project = {
    id: "p1",
    name: "Pipeline A",
    description: "Nightly training run",
    public: false,
    organizationId: "o1",
    experiments: [],
};

function renderRow(overrides: Partial<Parameters<typeof ProjectRow>[0]> = {}) {
    const onSettings = vi.fn();
    const onDelete = vi.fn();
    renderWithRouter(
        <Table>
            <TableBody>
                <ProjectRow
                    project={project}
                    href="/o1/projects/p1"
                    onSettings={onSettings}
                    onDelete={onDelete}
                    {...overrides}
                />
            </TableBody>
        </Table>,
    );
    return { onSettings, onDelete };
}

describe("ProjectRow", () => {
    it("links both the name and the secondary text to the project", () => {
        renderRow();
        const links = screen.getAllByRole("link");
        expect(links).toHaveLength(2);
        links.forEach((link) =>
            expect(link).toHaveAttribute("href", "/o1/projects/p1"),
        );
    });

    it("omits the secondary link when there is no description", () => {
        renderRow({ project: { ...project, description: "" } });
        expect(screen.getAllByRole("link")).toHaveLength(1);
    });

    it("names its overflow trigger after the project", () => {
        renderRow();
        expect(
            screen.getByRole("button", { name: /actions for pipeline a/i }),
        ).toBeInTheDocument();
    });

    it("calls back when a menu action is picked", async () => {
        const { onSettings, onDelete } = renderRow();

        await userEvent.click(
            screen.getByRole("button", { name: /actions for pipeline a/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: /settings/i }),
        );
        expect(onSettings).toHaveBeenCalledOnce();
        expect(onDelete).not.toHaveBeenCalled();

        await userEvent.click(
            screen.getByRole("button", { name: /actions for pipeline a/i }),
        );
        await userEvent.click(
            await screen.findByRole("menuitem", { name: /delete/i }),
        );
        expect(onDelete).toHaveBeenCalledOnce();
    });
});
