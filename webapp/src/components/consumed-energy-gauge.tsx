import { cn } from "@/helpers/utils";

/*
 * The "Consumed energy" gauge: one SVG whose ring, value and caption are placed
 * in the design's own coordinate space, so the geometry lives in the viewBox
 * and the gauge scales to whatever box its parent gives it.
 *
 * The arc is a fixed decorative sweep, not a proportion of the value: these
 * metrics are unbounded running totals with no maximum anywhere in the API, so
 * there is nothing to take a fraction of. The number in the middle is the data.
 * It is drawn only when there is a value — a zero gauge shows bare track, so an
 * empty range reads as empty rather than as some amount.
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
            {/*
             * The arc is decorative, so it stands for "there is something here"
             * rather than for a proportion: at zero there is nothing to mark and
             * the ring is left as bare track.
             */}
            {value > 0 && (
                <path
                    d={arcPath(ARC_SWEEP)}
                    stroke="var(--cc-lime)"
                    strokeWidth={STROKE}
                    strokeLinecap="butt"
                />
            )}
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
