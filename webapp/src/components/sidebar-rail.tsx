import * as React from "react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Organization } from "@/api/schemas";
import { cn } from "@/helpers/utils";
import AccountMenu from "./account-menu";
import { GlobalIcon } from "./icons/global-icon";
import { ProjectsIcon } from "./icons/projects-icon";
import { AccountIcon } from "./icons/account-icon";
import { MembersIcon } from "./icons/members-icon";

/*
 * The app's primary navigation: the destinations stacked at the top of a
 * vertical rail with the account item pinned to the bottom, and the same items
 * as a bottom bar below `md`. The rail's width lives in the `rail` token.
 *
 * Icons take their fill from `currentColor`, so colouring a control moves its
 * icon and label together — green for the page you are on, white otherwise.
 */

/*
 * A control in the rail: an icon above its label, green when it is the page you
 * are on and white otherwise.
 *
 * A plain button that forwards its props, so the destinations use it for
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
 * glyph; `GlossaryIcon` is still exported from its own module for whenever a
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
             * Account item, pinned to the bottom. The `mt-auto` and the
             * separation live on this wrapper rather than on the button:
             * padding inside the trigger would enlarge its hit area and drag
             * the popover's anchor edge up with it.
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
