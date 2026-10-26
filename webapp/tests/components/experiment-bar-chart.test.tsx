import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import ExperimentsBarChart from "@/components/experiment-bar-chart";

// Recharts 3 renders nothing inside a zero-sized ResponsiveContainer, and
// jsdom measures every element as 0x0 — give the container a size.
beforeAll(() => {
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
        width: 800,
        height: 450,
    } as DOMRect);
});
afterAll(() => {
    vi.restoreAllMocks();
});

describe("ExperimentsBarChart", () => {
    it("renders 'No data available' when given an empty report list", () => {
        render(
            <ExperimentsBarChart
                isPublicView={false}
                experimentsReportData={[]}
                onExperimentClick={vi.fn()}
                selectedExperimentId=""
                projectName="Demo"
            />,
        );
        expect(screen.getByText(/no data available/i)).toBeInTheDocument();
    });

    it("hides the export button in public view", () => {
        render(
            <ExperimentsBarChart
                isPublicView={true}
                experimentsReportData={[]}
                onExperimentClick={vi.fn()}
                selectedExperimentId=""
                projectName="Demo"
            />,
        );
        expect(
            screen.queryByRole("button", { name: /export/i }),
        ).not.toBeInTheDocument();
    });
});
