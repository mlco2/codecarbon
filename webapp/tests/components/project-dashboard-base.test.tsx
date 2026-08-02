import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

class NoopResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
// @ts-expect-error -- jsdom doesn't have it
globalThis.ResizeObserver = NoopResizeObserver;

// Recharts internals also need this in jsdom.
if (!HTMLCanvasElement.prototype.getContext) {
    HTMLCanvasElement.prototype.getContext = (() => null) as never;
}

// Radix Select uses these APIs that jsdom doesn't implement.
if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
}

vi.mock("@/api/runs", () => ({
    getRunEmissionsByExperiment: vi.fn().mockResolvedValue([]),
    getEmissionsTimeSeries: vi.fn(),
}));

import ProjectDashboardBase from "@/components/project-dashboard-base";
import { renderWithRouter } from "../test-utils";

const baseProps = {
    isPublicView: false,
    project: {
        id: "p1",
        name: "Demo",
        description: "",
        public: false,
        organizationId: "o1",
        experiments: [],
    },
    date: { from: new Date("2026-01-01"), to: new Date("2026-02-01") },
    onDateChange: vi.fn(),
    radialChartData: {
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    },
    convertedValues: { citizen: "0", transportation: "0", tvTime: "0" },
    experimentsReportData: [],
    runData: {
        experimentId: "",
        startDate: "2026-01-01T00:00:00Z",
        endDate: "2026-02-01T00:00:00Z",
    },
    selectedExperimentId: "",
    selectedRunId: "",
    onExperimentClick: vi.fn(),
    onRunClick: vi.fn(),
} as const;

describe("ProjectDashboardBase", () => {
    it("shows the empty-state message when there are no experiments", () => {
        renderWithRouter(
            <ProjectDashboardBase {...baseProps} projectExperiments={[]} />,
        );
        expect(
            screen.getByText(/no experiments have been created yet/i),
        ).toBeInTheDocument();
    });

    it("calls onExperimentClick with the picked id when an option is chosen", async () => {
        const onExperimentClick = vi.fn();
        renderWithRouter(
            <ProjectDashboardBase
                {...baseProps}
                onExperimentClick={onExperimentClick}
                projectExperiments={[
                    {
                        id: "exp-42",
                        name: "Run 1",
                        description: "first run",
                        project_id: "p1",
                    },
                ]}
            />,
        );
        await userEvent.click(screen.getByTestId("experiment-select"));
        await userEvent.click(screen.getByTestId("experiment-option-exp-42"));
        expect(onExperimentClick).toHaveBeenCalledWith("exp-42");
    });

    it("shows the selected experiment's description and id with a copy button", () => {
        renderWithRouter(
            <ProjectDashboardBase
                {...baseProps}
                selectedExperimentId="exp-42"
                projectExperiments={[
                    {
                        id: "exp-42",
                        name: "Run 1",
                        description: "first run",
                        project_id: "p1",
                    },
                ]}
            />,
        );
        const details = screen.getByTestId("experiment-details");
        expect(details).toHaveTextContent("first run");
        expect(details).toHaveTextContent("exp-42");
        expect(
            screen.getByRole("button", { name: /copy experiment id/i }),
        ).toBeInTheDocument();
    });
});
