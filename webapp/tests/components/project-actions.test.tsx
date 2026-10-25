import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/api/projects", () => ({ updateProject: vi.fn() }));
const runsApi = vi.hoisted(() => ({
    getEmissionsTimeSeries: vi.fn(),
    getRunEmissionsByExperiment: vi.fn(),
}));
vi.mock("@/api/runs", () => runsApi);
vi.mock("@/components/projectTokens/projectTokenTable", () => ({
    ProjectTokensTable: () => <div />,
}));

const exportToJsonMock = vi.hoisted(() => vi.fn());
vi.mock("@/utils/export", () => ({ exportToJson: exportToJsonMock }));

import ProjectActions from "@/components/project-actions";
import { ExperimentReport } from "@/api/schemas";

const project = {
    id: "p1",
    name: "Pipeline A",
    description: "Nightly run",
    public: false,
    organizationId: "o1",
    experiments: [],
};

const runData = {
    experimentId: "e1",
    startDate: "2024-01-01",
    endDate: "2024-02-01",
};

beforeEach(() => {
    exportToJsonMock.mockReset();
    runsApi.getEmissionsTimeSeries.mockReset();
    runsApi.getRunEmissionsByExperiment.mockReset();
    runsApi.getRunEmissionsByExperiment.mockResolvedValue([]);
});

function renderActions(experimentsReportData: ExperimentReport[] = []) {
    const onRefresh = vi.fn();
    render(
        <ProjectActions
            project={project}
            experimentsReportData={experimentsReportData}
            runData={runData}
            onRefresh={onRefresh}
        />,
    );
    return { onRefresh };
}

describe("ProjectActions", () => {
    it("offers the project's actions, each named", () => {
        renderActions();
        expect(
            screen.getByRole("button", { name: /refresh data/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /download json export/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /project settings/i }),
        ).toBeInTheDocument();
    });

    it("hides the share control while the project is private", () => {
        renderActions();
        expect(
            screen.queryByRole("button", { name: /share project/i }),
        ).not.toBeInTheDocument();
    });

    it("refreshes when asked", async () => {
        const { onRefresh } = renderActions();
        await userEvent.click(
            screen.getByRole("button", { name: /refresh data/i }),
        );
        await waitFor(() => expect(onRefresh).toHaveBeenCalledOnce());
    });

    it("exports the project as JSON", async () => {
        renderActions();
        await userEvent.click(
            screen.getByRole("button", { name: /download json export/i }),
        );
        await waitFor(() => expect(exportToJsonMock).toHaveBeenCalledOnce());

        const [payload] = exportToJsonMock.mock.calls[0];
        expect(payload.projects[0].id).toBe("p1");
        expect(payload.projects[0].date_range).toEqual({
            startDate: runData.startDate,
            endDate: runData.endDate,
        });
    });

    it("lets the export be retried after it fails", async () => {
        const experiment = {
            experiment_id: "e1",
            name: "Training",
        } as ExperimentReport;
        runsApi.getRunEmissionsByExperiment.mockRejectedValueOnce(
            new Error("offline"),
        );
        // A run whose emissions cannot be fetched still exports.
        runsApi.getRunEmissionsByExperiment.mockResolvedValueOnce([
            { runId: "r1", emissions: 1 },
        ]);
        runsApi.getEmissionsTimeSeries.mockResolvedValue(null);
        renderActions([experiment]);
        const button = screen.getByRole("button", {
            name: /download json export/i,
        });

        await userEvent.click(button);
        await waitFor(() => expect(button).toBeEnabled());

        await userEvent.click(button);
        await waitFor(() => expect(exportToJsonMock).toHaveBeenCalledOnce());
    });

    it("opens project settings in place", async () => {
        renderActions();
        await userEvent.click(
            screen.getByRole("button", { name: /project settings/i }),
        );
        expect(
            await screen.findByRole("heading", { name: /project settings/i }),
        ).toBeInTheDocument();
    });
});
