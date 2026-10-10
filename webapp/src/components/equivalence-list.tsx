import { cn } from "@/helpers/utils";

/*
 * The "Equal to" list: an icon, the figure it stands for, and a caption saying
 * what the figure means.
 *
 * One component for both dashboards, since the design draws the same item in
 * each. Only the direction differs: the global dashboard spreads them across the
 * width of its section, and the project dashboard stacks them in a column beside
 * its gauges. That is the `direction` prop, and it is the only thing a caller
 * decides — an item always looks the same.
 *
 * The captions wrap to two lines at the measure the design gives them, so the
 * column keeps its shape rather than stretching to the longest caption.
 */
export type Equivalence = {
    icon: string;
    alt: string;
    value: string;
    caption: string;
};

/*
 * The icon, wording and unit for each equivalence, declared once.
 *
 * Both dashboards compute these from the same helpers, so they must read the
 * same. They did not: the two pages had drifted to different captions for the
 * same number, and one of them rendered kilometres with no unit at all.
 *
 * The caption for the first is per-capita emissions, not household energy — that
 * is what `getEquivalentCitizenPercentage` divides by (a US citizen's yearly
 * CO2e, over 52 weeks). The design's own copy says "an american household weekly
 * energy consumption", which describes neither half of that.
 */
export function equivalences({
    citizen,
    transportation,
    tvTime,
}: {
    /** Percentage of a citizen's weekly emissions, already rounded. */
    citizen: string;
    /** Kilometres, already rounded. */
    transportation: string;
    /** Days, already rounded. */
    tvTime: string;
}): Equivalence[] {
    return [
        {
            icon: "/icons/household_consumption.svg",
            alt: "Household consumption icon",
            value: `${citizen}%`,
            caption: "Of a U.S. citizen's weekly emissions",
        },
        {
            icon: "/icons/transportation.svg",
            alt: "Transportation icon",
            value: `${transportation} km`,
            caption: "Kilometers ridden",
        },
        {
            icon: "/icons/tv.svg",
            alt: "TV icon",
            value: `${tvTime} days`,
            caption: "Of watching TV",
        },
    ];
}

export default function EquivalenceList({
    items,
    direction = "row",
    className,
}: Readonly<{
    items: Equivalence[];
    direction?: "row" | "column";
    className?: string;
}>) {
    return (
        <ul
            className={cn(
                direction === "row"
                    ? // Spread across the section, wrapping instead of
                      // overflowing once the column is too narrow to hold them.
                      "flex flex-wrap justify-between gap-x-12 gap-y-6 lg:gap-y-8"
                    : "flex flex-col gap-6 lg:gap-8",
                className,
            )}
        >
            {items.map((item) => (
                <li
                    key={item.caption}
                    className="flex min-w-0 items-center gap-4 lg:gap-6"
                >
                    <img
                        src={item.icon}
                        alt={item.alt}
                        width={50}
                        height={50}
                        className="size-10 shrink-0 lg:size-[50px]"
                    />
                    <div className="flex min-w-0 flex-col gap-2">
                        <p className="type-display type-stat-value text-cc-lime">
                            {item.value}
                        </p>
                        <p className="type-mono-medium type-stat-caption max-w-[15.5rem] break-words text-cc-white">
                            {item.caption}
                        </p>
                    </div>
                </li>
            ))}
        </ul>
    );
}
