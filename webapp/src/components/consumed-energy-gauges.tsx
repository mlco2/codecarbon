import ConsumedEnergyGauge from "./consumed-energy-gauge";
import { cn } from "@/helpers/utils";

/*
 * The "Consumed energy" gauges: energy, emissions and duration, each a ring with
 * its figure and unit.
 *
 * One component for both dashboards, as with the equivalences beside them — the
 * design draws the same three rings on each. The gauges keep their own size and
 * wrap when the row runs out of width, which is how the design lays them out (a
 * gap between them, not a distribution across the width).
 */
export type Gauge = {
    label: string;
    value: number;
};

export default function ConsumedEnergyGauges({
    gauges,
    className,
}: Readonly<{
    gauges: Gauge[];
    className?: string;
}>) {
    return (
        <ul className={cn("flex flex-wrap gap-6 lg:gap-9", className)}>
            {gauges.map((gauge) => (
                <li key={gauge.label} className="w-36 max-w-full sm:w-gauge">
                    <ConsumedEnergyGauge
                        value={gauge.value}
                        label={gauge.label}
                    />
                </li>
            ))}
        </ul>
    );
}
