import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NavItem from "@/components/nav-item";

describe("NavItem", () => {
    it("renders children and fires onClick", async () => {
        const onClick = vi.fn();
        render(
            <NavItem isSelected={false} onClick={onClick}>
                Dashboard
            </NavItem>,
        );

        const button = screen.getByRole("button", { name: /dashboard/i });
        await userEvent.click(button);
        expect(onClick).toHaveBeenCalledOnce();
    });

    it("applies the selected styling when isSelected is true", () => {
        render(<NavItem isSelected={true}>Home</NavItem>);
        const button = screen.getByRole("button", { name: /home/i });
        expect(button.className).toContain("text-primary");
    });
});
