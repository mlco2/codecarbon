import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import BreadcrumbHeader from "@/components/breadcrumb";
import { renderWithRouter } from "../test-utils";

describe("BreadcrumbHeader", () => {
    it("renders all segments and links the ones with hrefs", () => {
        renderWithRouter(
            <BreadcrumbHeader
                pathSegments={[
                    { title: "Org", href: "/org-1" },
                    { title: "Projects", href: "/org-1/projects" },
                    { title: "Project A", href: null },
                ]}
            />,
        );

        const orgLink = screen.getByRole("link", { name: /org/i });
        expect(orgLink).toHaveAttribute("href", "/org-1");
        expect(screen.getByRole("link", { name: /projects/i })).toHaveAttribute(
            "href",
            "/org-1/projects",
        );
        // Last segment (no href) is plain text, not a link.
        expect(screen.getByText("Project A").tagName).toBe("SPAN");
    });
});
