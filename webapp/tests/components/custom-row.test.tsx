import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CustomRow from "@/components/custom-row";
import { renderWithRouter } from "../test-utils";
import { Table, TableBody } from "@/components/ui/table";

function renderInTable(node: React.ReactNode) {
    return renderWithRouter(
        <Table>
            <TableBody>{node}</TableBody>
        </Table>,
    );
}

describe("CustomRow", () => {
    it("renders both columns", () => {
        renderInTable(
            <CustomRow
                rowKey="r1"
                firstColumn="Project A"
                secondColumn="An ML training pipeline"
            />,
        );
        expect(screen.getByText("Project A")).toBeInTheDocument();
        expect(screen.getByText("An ML training pipeline")).toBeInTheDocument();
    });

    it("triggers onDelete when the delete menu item is clicked", async () => {
        const onDelete = vi.fn().mockResolvedValue(undefined);
        renderInTable(
            <CustomRow
                rowKey="r1"
                firstColumn="A"
                secondColumn="B"
                onDelete={onDelete}
                deleteDisabled={false}
            />,
        );
        await userEvent.click(
            screen.getByRole("button", { name: /toggle project settings/i }),
        );
        await userEvent.click(
            screen.getByRole("menuitem", { name: /delete/i }),
        );
        expect(onDelete).toHaveBeenCalledOnce();
    });
});
