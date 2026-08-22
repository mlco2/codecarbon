import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import useSWR from "swr";

import { Organization } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import Loader from "@/components/loader";
import SidebarRail from "@/components/sidebar-rail";

/*
 * Shell for the redesigned dashboard.
 *
 * The design is an application viewport rather than a scrolling document: the
 * rail runs the full height with its "Account" item at the bottom, and the page
 * content fits without the page scrolling. So the shell is exactly one viewport
 * tall and distributes that height structurally — the rail and the content area
 * are siblings in a row, and the content column owns the only scroll.
 *
 * The `min-h-0` / `min-w-0` on the flex children is what makes that work: without
 * them the content's intrinsic size would stretch the shell and push the rail's
 * Account item off-screen. Nothing here subtracts the rail's width; the rail
 * declares its own width and the content takes what is left via `flex-1`.
 *
 * One navigation, two presentations, from a single `SidebarRail` instance: a
 * vertical rail beside the content from `md` up, and a bottom bar beneath it
 * below that. `flex-col-reverse` is what places it — the rail stays first in the
 * DOM, so it keeps its natural reading and tab order, while appearing last on
 * screen. Being in normal flow, the bar takes its own space instead of covering
 * the content.
 */
export default function DashboardLayout() {
    const [initialLoad, setInitialLoad] = useState(true);

    const { data: orgs, error } = useSWR<Organization[]>(
        "/organizations",
        fetcher,
        { revalidateOnFocus: false },
    );

    useEffect(() => {
        if (orgs || error) {
            const timer = setTimeout(() => {
                setInitialLoad(false);
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [orgs, error]);

    return (
        <div className="flex h-dvh w-full flex-col-reverse overflow-hidden bg-cc-background md:flex-row">
            <a
                href="#main-content"
                className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground"
            >
                Skip to main content
            </a>

            {/* The design's "Side Menu closed" — the vertical rail from
                `md` up, a bottom navigation bar below it. */}
            <SidebarRail orgs={orgs || []} />

            <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
                <main
                    id="main-content"
                    className="flex min-h-0 min-w-0 flex-1 flex-col"
                >
                    {initialLoad ? (
                        <div className="flex h-full items-center justify-center">
                            <Loader />
                        </div>
                    ) : (
                        <Outlet />
                    )}
                </main>
            </div>
        </div>
    );
}
