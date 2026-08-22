import { cn } from "@/helpers/utils";

/*
 * The "Consumed energy" gauge from the design.
 *
 * The whole gauge is one SVG, so its geometry lives in the viewBox rather than
 * in CSS offsets: the ring, the value and the caption are all placed in the
 * design's own coordinate space, exactly as Figma specifies them. That keeps the
 * numbers where they are meaningful (vector coordinates) instead of turning them
 * into layout margins, and — because the SVG scales to its box rather than
 * carrying a fixed pixel size — it lets the parent shrink the gauge on narrow
 * screens.
 *
 * Figma values, identical for all three gauges:
 *   viewBox      199.23 x 199.23
 *   ring         cx = cy = 99.6152, r = 87.0511, 25.1281 stroke
 *   track        #3B4041
 *   value arc    #BFFB4F, butt caps, sweeping anti-clockwise from 12 o'clock
 *   value        Disket Mono Bold 26, #BFFB4F, at 40.384 / 75.384
 *   caption      IBM Plex Mono Medium 13.343, #8A8A8A, at 43.974 / 115.769
 *
 * The arc is a fixed decorative sweep, not a proportion of the value. That is
 * deliberate and matches what this dashboard has always drawn: the previous
 * recharts gauges swept a constant 100 degrees regardless of their data, and
 * Figma gives the three gauges different arbitrary sweeps even where two show the
 * same number. These metrics are unbounded running totals with no maximum
 * anywhere in the API, so there is nothing to take a fraction of — the number in
 * the middle is the data.
 *
 * What changed from the old gauges is presentation only: the arc was rendering
 * black (its fill never resolved), and it started at 3 o'clock. It is now the
 * design's lime and starts at 12 o'clock.
 */

const VIEWBOX = 199.23;
const CENTER = 99.6152;
const RADIUS = 87.0511;
const STROKE = 25.1281;

/** 12 o'clock, in the screen degrees used below (0 = 3 o'clock, clockwise). */
const START_ANGLE = 270;
/** The sweep the previous gauges drew, kept so the rings look unchanged. */
const ARC_SWEEP = 100;

const point = (angleDeg: number) => {
    const a = (angleDeg * Math.PI) / 180;
    return [CENTER + RADIUS * Math.cos(a), CENTER + RADIUS * Math.sin(a)];
};

/** Arc sweeping anti-clockwise from 12 o'clock by `sweep` degrees. */
function arcPath(sweep: number) {
    const [x0, y0] = point(START_ANGLE);
    const [x1, y1] = point(START_ANGLE - sweep);
    const largeArc = sweep > 180 ? 1 : 0;
    // sweep-flag 0 draws anti-clockwise in SVG's y-down coordinate system.
    return `M ${x0} ${y0} A ${RADIUS} ${RADIUS} 0 ${largeArc} 0 ${x1} ${y1}`;
}

export default function ConsumedEnergyGauge({
    value,
    label,
    className,
}: Readonly<{
    /** The metric's value, shown in the middle of the ring. */
    value: number;
    /** Unit caption, e.g. "kWh". */
    label: string;
    className?: string;
}>) {
    return (
        <svg
            viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            role="img"
            aria-label={`${value} ${label}`}
            className={cn("h-auto w-full", className)}
        >
            <circle
                cx={CENTER}
                cy={CENTER}
                r={RADIUS}
                stroke="var(--cc-gauge-track)"
                strokeWidth={STROKE}
            />
            <path
                d={arcPath(ARC_SWEEP)}
                stroke="var(--cc-lime)"
                strokeWidth={STROKE}
                strokeLinecap="butt"
            />
            {/*
             * Figma left-aligns both labels from their own x offsets, with the
             * value's baseline box starting at y 75.384 and the caption's at
             * 115.769. `dominant-baseline: text-before-edge` makes those the top
             * edges, matching how Figma positions the text frames.
             */}
            <text
                x={40.384}
                y={75.384}
                dominantBaseline="text-before-edge"
                fill="var(--cc-lime)"
                className="type-display type-gauge-value"
            >
                {value}
            </text>
            <text
                x={43.974}
                y={115.769}
                dominantBaseline="text-before-edge"
                fill="var(--cc-gauge-label)"
                className="type-mono-medium type-gauge-label"
            >
                {label}
            </text>
        </svg>
    );
}
