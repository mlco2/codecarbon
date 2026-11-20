import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import ProjectVisibilityBadge from "@/components/project-visibility-badge";

describe("ProjectVisibilityBadge", () => {
    it("says Public when the project is public", () => {
        render(<ProjectVisibilityBadge isPublic />);
        expect(screen.getByText("Public")).toBeInTheDocument();
    });

    it("says Private otherwise", () => {
        render(<ProjectVisibilityBadge isPublic={false} />);
        expect(screen.getByText("Private")).toBeInTheDocument();
    });
});
