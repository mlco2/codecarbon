import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

class NoopResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
// @ts-expect-error -- jsdom doesn't have it
globalThis.ResizeObserver = NoopResizeObserver;

import RadialChart from "@/components/radial-chart";

describe("RadialChart", () => {
    it("falls back to 'No data available' when value is undefined", () => {
        render(
            // @ts-expect-error -- testing the missing-value branch
            <RadialChart data={{ label: "kWh" }} />,
        );
        expect(screen.getByText(/no data available/i)).toBeInTheDocument();
    });

    it("does not show the empty-state when value is defined", () => {
        render(<RadialChart data={{ label: "kWh", value: 12.34 }} />);
        // The fallback is hidden when a value is provided. We don't assert
        // on Recharts SVG output because jsdom doesn't measure layout, so
        // the chart never reaches the rendered phase here.
        expect(
            screen.queryByText(/no data available/i),
        ).not.toBeInTheDocument();
    });
});
