import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";

import { Breadcrumb } from "@/components/ui/breadcrumb";
import { renderWithRouter } from "../test-utils";

describe("Breadcrumb", () => {
    it("links every crumb that has a destination", () => {
        renderWithRouter(
            <Breadcrumb
                items={[
                    { label: "Mozilla", to: "/o1" },
                    { label: "Projects", to: "/o1/projects" },
                    { label: "Bench" },
                ]}
            />,
        );

        const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
        expect(
            within(nav).getByRole("link", { name: "Mozilla" }),
        ).toHaveAttribute("href", "/o1");
        expect(
            within(nav).getByRole("link", { name: "Projects" }),
        ).toHaveAttribute("href", "/o1/projects");
        expect(within(nav).queryByRole("link", { name: "Bench" })).toBeNull();
    });

    /*
     * The organisation dashboard's first crumb has nowhere to go either, so
     * "not a link" and "the page you are on" have to stay separate: only the
     * last crumb is current, and only it is green.
     */
    it("marks the last crumb as the current page, not every unlinked one", () => {
        renderWithRouter(
            <Breadcrumb items={[{ label: "Mozilla" }, { label: "Global" }]} />,
        );

        const current = screen.getAllByText(
            (_, element) => element?.getAttribute("aria-current") === "page",
        );
        expect(current).toHaveLength(1);
        expect(current[0]).toHaveTextContent("Global");
    });

    it("separates crumbs with a spaced slash", () => {
        renderWithRouter(
            <Breadcrumb
                items={[{ label: "Mozilla", to: "/o1" }, { label: "Members" }]}
            />,
        );

        expect(
            screen.getByRole("navigation", { name: "Breadcrumb" }),
        ).toHaveTextContent("Mozilla / Members");
    });
});
