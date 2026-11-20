import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { FormField } from "@/components/ui/form-field";

describe("FormField", () => {
    it("ties its label to its control", () => {
        render(<FormField id="token-name" label="Token name" />);
        expect(screen.getByLabelText("Token name")).toBe(
            screen.getByRole("textbox"),
        );
    });

    it("keeps the accessible name when the label is hidden", () => {
        render(<FormField id="email" label="Email address" hideLabel />);
        // Still reachable by name, but not shown as a visible label.
        expect(screen.getByLabelText("Email address")).toBeInTheDocument();
        expect(screen.getByText("Email address")).toHaveClass("sr-only");
    });
});
