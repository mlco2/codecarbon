import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import ConsumedEnergyGauge from "@/components/consumed-energy-gauge";

/*
 * The arc stands for "there is something here", so an empty range must not draw
 * it — otherwise a zero gauge looks like some amount.
 */
describe("ConsumedEnergyGauge", () => {
    it("draws the arc when there is a value", () => {
        const { container } = render(
            <ConsumedEnergyGauge value={12.5} label="kWh" />,
        );
        expect(container.querySelector("path")).not.toBeNull();
    });

    it("draws no arc at zero", () => {
        const { container } = render(
            <ConsumedEnergyGauge value={0} label="kWh" />,
        );
        expect(container.querySelector("path")).toBeNull();
        // The track and the figures stay.
        expect(container.querySelector("circle")).not.toBeNull();
        expect(screen.getByText("0")).toBeInTheDocument();
    });

    it("names itself with its value and unit", () => {
        render(<ConsumedEnergyGauge value={3} label="days" />);
        expect(screen.getByRole("img", { name: "3 days" })).toBeInTheDocument();
    });
});
