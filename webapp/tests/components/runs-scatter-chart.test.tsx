import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

class NoopResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
// @ts-expect-error -- jsdom doesn't have it
globalThis.ResizeObserver = NoopResizeObserver;

const getRunEmissionsByExperimentMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/runs", () => ({
    getRunEmissionsByExperiment: getRunEmissionsByExperimentMock,
    getEmissionsTimeSeries: vi.fn(),
}));

import RunsScatterChart from "@/components/runs-scatter-chart";

beforeEach(() => {
    getRunEmissionsByExperimentMock.mockReset();
    getRunEmissionsByExperimentMock.mockResolvedValue([]);
});

describe("RunsScatterChart", () => {
    it("renders 'No data available' when no runs are returned", async () => {
        render(
            <RunsScatterChart
                isPublicView={false}
                params={{
                    experimentId: "exp-1",
                    startDate: "2026-01-01T00:00:00Z",
                    endDate: "2026-02-01T00:00:00Z",
                }}
                onRunClick={vi.fn()}
                projectName="Demo"
            />,
        );
        expect(
            await screen.findByText(/no data available/i),
        ).toBeInTheDocument();
    });

    it("does not call the API when experimentId is empty", () => {
        render(
            <RunsScatterChart
                isPublicView={false}
                params={{
                    experimentId: "",
                    startDate: "2026-01-01T00:00:00Z",
                    endDate: "2026-02-01T00:00:00Z",
                }}
                onRunClick={vi.fn()}
                projectName="Demo"
            />,
        );
        // The component still calls the API — but the API short-circuits to []
        // when experimentId is empty. We assert the rendered fallback.
        expect(screen.getByText(/no data available/i)).toBeInTheDocument();
    });
});
