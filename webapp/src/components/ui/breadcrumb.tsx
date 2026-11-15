import { Fragment } from "react";
import { Link } from "react-router-dom";

import { cn } from "@/helpers/utils";

/*
 * The redesign's breadcrumb: mono labels in grey, separated by a spaced slash,
 * with the page you are on closing the trail in the button green.
 *
 * A crumb links unless it has no `to` — the last one never does, and the
 * organisation dashboard's own name does not either, since it is the page's
 * own root. Only the last crumb is the current page.
 *
 * Every trail in the app is a flat list of labels where all but the last one
 * link somewhere, so the component takes that list rather than composed
 * children — the pages were otherwise repeating the same nav, the same two
 * colour classes and the same separator four times over.
 *
 * The separator sits outside the link so hovering a crumb lights the label
 * alone, and it is hidden from assistive tech, which reads the list structure
 * instead.
 */

export type BreadcrumbItem = {
    label: string;
    /** Omit on the final crumb, and wherever a crumb has nowhere to go. */
    to?: string;
};

export function Breadcrumb({
    items,
    className,
}: {
    items: BreadcrumbItem[];
    /** Spacing below the trail, which differs per page. */
    className?: string;
}) {
    return (
        <nav
            aria-label="Breadcrumb"
            className={cn("type-mono-medium type-breadcrumb", className)}
        >
            <ol className="inline">
                {items.map((item, index) => {
                    const isLast = index === items.length - 1;

                    return (
                        <Fragment key={`${item.label}-${index}`}>
                            {index > 0 && (
                                <li
                                    aria-hidden="true"
                                    className="inline text-cc-breadcrumb-gray"
                                >
                                    {" / "}
                                </li>
                            )}
                            <li className="inline">
                                {item.to ? (
                                    <Link
                                        to={item.to}
                                        className="text-cc-breadcrumb-gray transition-colors hover:text-cc-white motion-reduce:transition-none"
                                    >
                                        {item.label}
                                    </Link>
                                ) : isLast ? (
                                    <span
                                        aria-current="page"
                                        className="text-cc-button-hover"
                                    >
                                        {item.label}
                                    </span>
                                ) : (
                                    <span className="text-cc-breadcrumb-gray">
                                        {item.label}
                                    </span>
                                )}
                            </li>
                        </Fragment>
                    );
                })}
            </ol>
        </nav>
    );
}
