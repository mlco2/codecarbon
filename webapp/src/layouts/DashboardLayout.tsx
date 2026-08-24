import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import useSWR from "swr";

import { Organization } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import Loader from "@/components/loader";
import SidebarRail from "@/components/sidebar-rail";

/*
 * Shell for the redesigned dashboard: exactly one viewport tall, with the rail
 * and the content area as siblings in a row and the content column owning the
 * only scroll.
 *
 * The `min-h-0` / `min-w-0` on the flex children is what makes that work —
 * without them the content's intrinsic size stretches the shell and pushes the
 * rail's Account item off-screen. `flex-col-reverse` puts the mobile bar below
 * the content while leaving the rail first in the DOM, so it keeps its reading
 * and tab order.
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
