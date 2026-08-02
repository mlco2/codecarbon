import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorMessage from "@/components/error-message";

describe("ErrorMessage", () => {
    it("renders a generic error alert", () => {
        render(<ErrorMessage />);
        expect(screen.getByText(/an error occurred/i)).toBeInTheDocument();
        expect(screen.getByText(/contact support/i)).toBeInTheDocument();
    });
});
