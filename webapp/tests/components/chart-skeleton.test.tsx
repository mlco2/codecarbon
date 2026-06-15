import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import ChartSkeleton from "@/components/chart-skeleton";

describe("ChartSkeleton", () => {
    it("uses the default 250px height when none is supplied", () => {
        const { container } = render(<ChartSkeleton />);
        const chartArea = container.querySelector("[style*='height: 250px']");
        expect(chartArea).not.toBeNull();
    });

    it("respects a custom height prop", () => {
        const { container } = render(<ChartSkeleton height={400} />);
        const chartArea = container.querySelector("[style*='height: 400px']");
        expect(chartArea).not.toBeNull();
    });
});
