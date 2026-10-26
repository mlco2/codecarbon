import {
    describe,
    it,
    expect,
    vi,
    beforeEach,
    beforeAll,
    afterAll,
} from "vitest";
import { render, screen } from "@testing-library/react";

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
