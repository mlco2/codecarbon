import { cn } from "@/helpers/utils";

/*
 * Two charts side by side, separated by a rule.
 *
 * The rules read as one cross across the four charts, so nothing here is spaced
 * with margins: the gap around a rule is padding *inside* the cells, which leaves
 * the rule running the full height of the row. A margin would end the line early
 * and break the cross at its centre.
 *
 * The inset is a prop rather than something a caller passes through `className`:
 * these are arbitrary variants, so a `[&>*:first-child]` rule outranks a `[&>*]`
 * one whatever the class order, and an override would reach one cell only.
 *
 * The cells arrive wrapped in `Suspense` and fragments, which render no DOM node,
 * so the inset reaches them through child selectors rather than by the caller
 * putting it on each chart.
 *
 * Below `md` the columns stack and the rule turns horizontal with them.
 */
export default function ChartRow({
    insetTop = false,
    insetBottom = false,
    className,
    children,
}: Readonly<{
    /** Space above the charts, for a row sitting under a rule. */
    insetTop?: boolean;
    /** Space below them, for a row sitting above one. */
    insetBottom?: boolean;
    className?: string;
    children: React.ReactNode;
}>) {
    return (
        <div
            className={cn(
                "grid grid-cols-1 divide-y divide-cc-rule md:grid-cols-2 md:divide-x md:divide-y-0",
                // Stacked: the rule sits between them, with equal space either
                // side. Scoped to below `md` rather than reset above it — a
                // `[&>*:first-child]` reset outranks the `[&>*]` inset below and
                // would silently apply it to one cell only.
                "max-md:[&>*:first-child]:pb-10 max-md:[&>*:last-child]:pt-10",
                // Side by side: equal space either side of the vertical rule.
                "md:[&>*:first-child]:pr-10 md:[&>*:last-child]:pl-10",
                "lg:[&>*:first-child]:pr-16 lg:[&>*:last-child]:pl-16",
                // Applied to both cells, so the row's own edges stay level.
                insetTop && "md:[&>*]:pt-10 lg:[&>*]:pt-16",
                insetBottom && "md:[&>*]:pb-10 lg:[&>*]:pb-16",
                className,
            )}
        >
            {children}
        </div>
    );
}
