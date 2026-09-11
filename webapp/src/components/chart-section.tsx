import { cn } from "@/helpers/utils";

/*
 * A titled block of the dashboard: heading, a line saying what it is for, and
 * whatever action belongs to it, above the thing itself.
 *
 * The charts each drew this by hand inside a `Card`. They share it now, so the
 * page reads as one surface with sections on it rather than a wall of boxes, and
 * the three headings cannot drift apart. It carries no border or fill of its own:
 * the panels behind the redesign are the page, not the card.
 */
export default function ChartSection({
    title,
    description,
    action,
    className,
    children,
}: Readonly<{
    title: string;
    description?: string;
    /** Sits on the title's row, at its end. */
    action?: React.ReactNode;
    className?: string;
    children: React.ReactNode;
}>) {
    return (
        <section className={cn("flex flex-col gap-6", className)}>
            <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
                    <h3 className="type-display type-section-title min-w-0 text-cc-white">
                        {title}
                    </h3>
                    {action}
                </div>
                {description && (
                    <p className="type-mono-medium type-stat-caption text-cc-gray">
                        {description}
                    </p>
                )}
            </div>
            {children}
        </section>
    );
}
