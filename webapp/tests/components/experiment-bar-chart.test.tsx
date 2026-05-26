import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ExperimentsBarChart from "@/components/experiment-bar-chart";

// Recharts uses ResizeObserver / canvas — silence them in jsdom.
class NoopResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
// @ts-expect-error -- jsdom doesn't have it
globalThis.ResizeObserver = NoopResizeObserver;

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
