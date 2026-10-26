import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import EquivalenceList, { equivalences } from "@/components/equivalence-list";

/*
 * Both dashboards render these from one builder, so the captions and units
 * cannot drift apart again — they did once, and one page showed kilometres with
 * no unit at all.
 */
describe("equivalences", () => {
    it("carries the unit on every figure", () => {
        const [citizen, transport, tv] = equivalences({
            citizen: "1.50",
            transportation: "42.00",
            tvTime: "7.00",
        });

        expect(citizen.value).toBe("1.50%");
        expect(transport.value).toBe("42.00 km");
        expect(tv.value).toBe("7.00 days");
    });

    it("describes the first figure as a citizen's emissions, which is what it is", () => {
        const [citizen] = equivalences({
            citizen: "1",
            transportation: "1",
            tvTime: "1",
        });
        expect(citizen.caption).toMatch(/citizen/i);
        expect(citizen.caption).toMatch(/emissions/i);
    });
});

describe("EquivalenceList", () => {
    it("renders a figure and caption per item", () => {
        render(
            <EquivalenceList
                items={equivalences({
                    citizen: "1.50",
                    transportation: "42.00",
                    tvTime: "7.00",
                })}
            />,
        );

        expect(screen.getByText("1.50%")).toBeInTheDocument();
        expect(screen.getByText("42.00 km")).toBeInTheDocument();
        expect(screen.getByText("7.00 days")).toBeInTheDocument();
        expect(screen.getAllByRole("listitem")).toHaveLength(3);
    });
});
