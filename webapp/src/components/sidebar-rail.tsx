import * as React from "react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Organization } from "@/api/schemas";
import { cn } from "@/helpers/utils";
import AccountMenu from "./account-menu";
import { GlobalIcon, ProjectsIcon } from "./icons/figma-icons";
import { AccountIcon } from "./icons/account-icon";
import { MembersIcon } from "./icons/members-icon";

/*
 * The "Side Menu closed" rail from the design.
 *
 * Figma positions the rail's groups as absolutely placed children with
 * percentage insets, but they are structurally just a column: the destinations
 * stacked at the top, then the account item at the bottom. That is what this
 * builds — two flex children, with `md:mt-auto` on the account wrapper — so the
 * rail's own padding and gaps produce the design's spacing instead of
 * coordinates doing it.
 *
 * The rail's width is its own dimension and lives in one place: the `rail`
 * spacing token. Nothing else in the app repeats it.
 *
 * Below `md` the same items render as a bottom navigation bar rather than a
 * rail, so this one component is the whole of the app's primary navigation: the
 * `nav` flips to a row and the destination group collapses to `display:
 * contents` so all four items space evenly across it. Icons and labels step down
 * (32 -> 24px icons, and `type-rail-label` is 12px below `md` against 14px
 * above). See `DashboardLayout` for how the two presentations are placed.
 *
 * The frame draws a hamburger above the logo. Neither is rendered here: the
 * navigation is always visible in both presentations, so a control to reveal it
 * has nothing to do. (Confirmed with the project owners as a slip in the frame.)
 * Because nothing sits above the destinations, the rail's items begin directly
 * below its top padding rather than at the frame's y offsets.
 *
 * Figma spacing, mapped to the scale:
 *   rail padding      24px top (2.44%), 16px bottom (1.46%), 16px sides (16.83%)
 *   nav gap           24px
 *   nav item          10px padding, 32px icon, 8px gap, 14px label
 *   account           8px gap, 14px label
 *
 * The account item departs from the frame in one respect: the design draws a
 * 24px avatar, and this renders the 32px account icon so it matches the size of
 * every other item in the rail.
 *
 * The design also carries a fixed 228px height on its nav group that is smaller
 * than the group's own content (3x78 + 2x24 = 282px). Figma lets it overflow, so
 * the height is left to the content here, which is what the frame renders.
 *
 * Selected state: the icon and label turn #BFFB4F (Global, in this frame);
 * unselected items are #FFFFFF. Both use the same vector with a colour change.
 *
 * Hover and pressed states are not drawn in the frame. They are built from the
 * palette the design already uses: hover goes to #a0c55b (the design's own
 * "Button-hover" token) and pressing goes to #BFFB4F, the selected colour. The
 * icons take their fill from `currentColor`, so colouring the control moves the
 * icon and its label together with no extra rules.
 */

/*
 * A control in the rail: an icon above its label, green when it is the page you
 * are on and white otherwise.
 *
 * Hover and pressed are not drawn in the design, so they are built from the
 * palette it already uses — hover goes to its own "Button-hover" (#a0c55b) and
 * pressing to the selected green. The icons take their fill from `currentColor`,
 * so colouring the control moves the icon and its label together.
 *
 * It renders a plain button and forwards its props, so the destinations use it for
 * navigation and the account control uses it as a menu trigger.
 */
const RailButton = React.forwardRef<
    HTMLButtonElement,
    React.ComponentPropsWithoutRef<"button"> & {
        icon: (props: { className?: string }) => React.JSX.Element;
        label: string;
        isSelected?: boolean;
    }
>(({ icon: Icon, label, isSelected, className, ...props }, ref) => (
    <button
        ref={ref}
        type="button"
        aria-current={isSelected ? "page" : undefined}
        className={cn(
            "flex flex-1 cursor-pointer flex-col items-center gap-1 p-1.5 outline-none transition-colors",
            "md:flex-none md:gap-2 md:p-2.5",
            "hover:text-cc-button-hover active:text-cc-lime",
            "focus-visible:ring-2 focus-visible:ring-cc-lime",
            isSelected ? "text-cc-lime" : "text-cc-white",
            "motion-reduce:transition-none",
            className,
        )}
        {...props}
    >
        <Icon className="size-6 shrink-0 md:size-8" />
        <span className="type-mono-medium type-rail-label text-center">
            {label}
        </span>
    </button>
));
RailButton.displayName = "RailButton";

type RailItem = {
    key: string;
    label: string;
    Icon: (props: { className?: string }) => React.JSX.Element;
    path: (orgId: string) => string;
};

/*
 * The third item is Members, matching the destination it has always pointed at
 * (`/:organizationId/members`). Figma labels it "Glossary" and draws a different
 * glyph; `GlossaryIcon` is still exported from `figma-icons.tsx` for whenever a
 * glossary page exists.
 */
const ITEMS: RailItem[] = [
    { key: "global", label: "Global", Icon: GlobalIcon, path: (o) => `/${o}` },
    {
        key: "projects",
        label: "Projects",
        Icon: ProjectsIcon,
        path: (o) => `/${o}/projects`,
    },
    {
        key: "members",
        label: "Members",
        Icon: MembersIcon,
        path: (o) => `/${o}/members`,
    },
];

export default function SidebarRail({
    orgs,
    className,
}: Readonly<{
    orgs: Organization[] | undefined;
    className?: string;
}>) {
    const { pathname } = useLocation();
    const navigate = useNavigate();

    // Same selected-organization resolution the previous nav used, so the
    // localStorage contract and URL-derived org are unchanged.
    const [selectedOrg, setSelectedOrg] = useState<string | null>(() => {
        try {
            return localStorage.getItem("organizationId");
        } catch {
            return null;
        }
    });

    useEffect(() => {
        if (selectedOrg) return;
        try {
            const localOrg = localStorage.getItem("organizationId");
            const found = orgs?.find((org) => org.id === localOrg);
            if (localOrg && found) {
                setSelectedOrg(localOrg);
            } else if (orgs && orgs.length > 0) {
                setSelectedOrg(orgs[0].id);
            }
        } catch (error) {
            console.error("Error reading from localStorage:", error);
        }
    }, [selectedOrg, orgs]);

    useEffect(() => {
        if (!selectedOrg) return;
        try {
            if (localStorage.getItem("organizationId") !== selectedOrg) {
                localStorage.setItem("organizationId", selectedOrg);
            }
            const orgName = orgs?.find((org) => org.id === selectedOrg)?.name;
            if (orgName) {
                localStorage.setItem("organizationName", orgName);
            }
        } catch (error) {
            console.error("Error writing to localStorage:", error);
        }
    }, [selectedOrg, orgs]);

    // Keep the rail in step with the org in the URL.
    useEffect(() => {
        const orgId = pathname.split("/")[1];
        if (orgId && orgs?.some((org) => org.id === orgId)) {
            setSelectedOrg(orgId);
        }
    }, [pathname, orgs]);

    const selectedKey = pathname.includes("/projects")
        ? "projects"
        : pathname.includes("/members")
          ? "members"
          : "global";

    return (
        <nav
            aria-label="Primary"
            className={cn(
                "shrink-0 bg-cc-background",
                // Mobile: a bottom bar. Its four items sit on one row, so the
                // groups below collapse to `display: contents` and let the nav
                // itself space them.
                "flex w-full flex-row items-stretch justify-around border-t-2 border-black px-2 py-1.5",
                // From `md`: the design's vertical rail.
                "md:h-full md:w-rail md:flex-col md:items-center md:justify-start md:overflow-y-auto md:border-r-2 md:border-t-0 md:px-4 md:pb-4 md:pt-6",
                className,
            )}
        >
            {/* Destinations */}
            <div className="contents md:flex md:w-full md:flex-col md:gap-6">
                {ITEMS.map(({ key, label, Icon, path }) => (
                    <RailButton
                        key={key}
                        icon={Icon}
                        label={label}
                        isSelected={key === selectedKey}
                        onClick={() => {
                            if (!selectedOrg) return;
                            navigate(path(selectedOrg));
                        }}
                    />
                ))}
            </div>

            {/*
             * Account item, pinned to the bottom of
             * the rail. Triggers the account menu, which opens upward from it.
             *
             * The `mt-auto` and the minimum separation live on this wrapper, not
             * on the button: padding inside the trigger would enlarge its hit
             * area and drag the popover's anchor edge up with it.
             */}
            <div className="flex flex-1 md:mt-auto md:w-full md:flex-none md:pt-6">
                <AccountMenu
                    orgs={orgs}
                    selectedOrg={selectedOrg}
                    onSelectOrg={(organizationId) => {
                        setSelectedOrg(organizationId);
                        navigate(`/${organizationId}`);
                    }}
                >
                    <RailButton
                        icon={AccountIcon}
                        label="Account"
                        className="w-full flex-none md:p-0"
                    />
                </AccountMenu>
            </div>
        </nav>
    );
}
