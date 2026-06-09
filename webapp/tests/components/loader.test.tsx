import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Loader from "@/components/loader";

describe("Loader", () => {
    it("exposes an accessible loading status", () => {
        render(<Loader />);
        const status = screen.getByRole("status");
        expect(status).toBeInTheDocument();
        expect(status).toHaveTextContent(/loading/i);
    });
});
