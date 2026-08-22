import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useSWR from "swr";

import { getOrganizations } from "@/api/organizations";
import { Organization, OrganizationUser, User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { cn } from "@/helpers/utils";
import { useModal } from "@/hooks/useModal";
import CreateOrganizationModal from "./createOrganizationModal";
import { ExitToAppIcon, SettingsIcon } from "./icons/figma-icons";
import { OrganizationIcon } from "./icons/organization-icon";
import { PlusIcon } from "./icons/plus-icon";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "./ui/dropdown-menu";

/*
 * The account menu from Figma 218:14541 ("menu"), the subject of frame
 * 218:7838 — "Changing organization from side bar".
 *
 * The panel is one of the few places where fixed dimensions are the right answer:
 * its width and row height are the component's own size, not a position, so they
 * live in the `menu` and `control` spacing tokens. Everything inside is a flex
 * column whose spacing comes from padding and gaps, and the panel's height is
 * whatever its rows add up to — it grows and shrinks with the real organization
 * list rather than being pinned to the frame's 338px.
 *
 * Figma values:
 *   panel   203px wide, #181818, 2px #a0c55b border, 4px radius,
 *           drop-shadow 0 4px 10px rgba(0,0,0,0.25)
 *   heading Inter Medium 10px, centred, 15px vertical padding (218:14542)
 *   row     46px tall, 15px/8px padding, 4px gap, 24px avatar,
 *           IBM Plex Mono Medium 12px label
 *   rule    1px #949494 with 10px either side (218:14547)
 *
 * Deviation from the frame: the design's rows carry a 2px #a0c55b edge on both
 * the left and the right when highlighted; only the right edge is kept here.
 *
 * Anchoring is expressed as a relationship to the trigger rather than as frame
 * coordinates. In the design the panel occupies x 49..252, y 621..959 and the
 * "Account" item occupies x 9..93, y 959..1009, which means:
 *   - the panel's bottom edge sits on the trigger's top edge  -> sideOffset 0
 *   - the panel's left edge sits at the trigger's centre      -> align start,
 *     shifted by half the trigger's width
 * The second is taken from Radix's own trigger-width variable, so it holds if the
 * rail's width or padding ever change.
 *
 * State: the menu is drawn open in Figma only to document its open appearance.
 * It is closed by default here and driven by real `open` state.
 *
 * The highlighted "Mozilla" row in the frame is an instance override rather than
 * a component variant — the Figma "menu item" component has a single "Default"
 * variant, so the design defines exactly one highlight treatment and does not
 * distinguish hover from selected. That one treatment is used for both here: it
 * persistently marks the organization currently being viewed, and it is also the
 * hover/focus state.
 */

/*
 * The row label fills the remaining width instead of carrying Figma's fixed
 * 121px text box, so long organization names wrap rather than overflow.
 */
const ROW =
    "min-h-control w-full flex items-center gap-1 px-4 py-2 " +
    "cursor-pointer select-none outline-none rounded-none " +
    "border-y-0 border-l-0 border-r-0 border-transparent " +
    // Reaches only the icons: every label sets its own colour below.
    "text-cc-gray";

/*
 * The highlight treatment, from Figma 218:14545: a #2b2b2b fill with a 2px
 * #a0c55b right edge and a #a0c55b label. The design also draws a matching left
 * edge; that one is dropped here by request. It serves two purposes
 * — it marks the organization you are currently viewing, and it is the
 * hover/focus state for any row. Focus is bound as well as hover so the menu is
 * fully operable from the keyboard; Radix moves focus with the arrow keys and
 * also sets it on hover.
 */
const ROW_HIGHLIGHT =
    "bg-cc-darkest-gray border-cc-button-hover text-cc-button-hover";
const ROW_HOVER =
    "focus:bg-cc-darkest-gray focus:border-cc-button-hover focus:text-cc-button-hover " +
    "data-[highlighted]:bg-cc-darkest-gray data-[highlighted]:border-cc-button-hover " +
    "data-[highlighted]:text-cc-button-hover";

const ROW_LABEL =
    "type-mono-medium type-menu-item min-w-0 flex-1 break-words " +
    "group-focus:text-cc-button-hover " +
    "group-data-[highlighted]:text-cc-button-hover";

function MenuRow({
    onSelect,
    children,
    icon,
    /** Marks the organization currently being viewed. */
    isCurrent,
}: Readonly<{
    onSelect: () => void;
    children: React.ReactNode;
    icon: React.ReactNode;
    isCurrent?: boolean;
}>) {
    return (
        <DropdownMenuItem
            className={cn("group", ROW, ROW_HOVER, isCurrent && ROW_HIGHLIGHT)}
            onSelect={onSelect}
            aria-current={isCurrent ? "true" : undefined}
        >
            {icon}
            <span
                className={cn(
                    ROW_LABEL,
                    isCurrent ? "text-cc-button-hover" : "text-cc-white",
                )}
            >
                {children}
            </span>
        </DropdownMenuItem>
    );
}

export default function AccountMenu({
    orgs,
    selectedOrg,
    onSelectOrg,
    children,
}: Readonly<{
    orgs: Organization[] | undefined;
    selectedOrg: string | null;
    onSelectOrg: (organizationId: string) => void;
    /** The rail's "Account" item, used as the trigger. */
    children: React.ReactNode;
}>) {
    const [open, setOpen] = useState(false);
    const navigate = useNavigate();
    const newOrgModal = useModal();
    /*
     * Holds the list only after creating an organization, so the new one shows up
     * without a reload. It deliberately starts undefined rather than mirroring
     * `orgs`: `orgs` arrives empty on the first render while SWR is still
     * fetching, and seeding state from it would freeze the menu on that empty
     * array. Until a refresh happens the live prop is used.
     */
    const [organizationList, setOrganizationList] = useState<
        Organization[] | undefined
    >(undefined);

    // The user's real name for the profile row. Figma shows a person's name and
    // photograph here; "Inimaz" is demo content and is not hardcoded. This uses
    // the endpoint AuthGuard already relies on, so no new API surface is added.
    const { data: auth } = useSWR<{ user?: User }>("/auth/check", fetcher, {
        revalidateOnFocus: false,
    });

    const list = organizationList ?? orgs;

    /*
     * Dashboards the user administers go below the rule; the rest are ones they
     * were invited to. Admin rights live on the membership, and the API exposes
     * them only per organization via its member list (`is_admin` on
     * `GET /organizations/{id}/users`), so this asks each organization in turn.
     *
     * Deferred until the menu is opened, to keep it off the page-load path, and
     * cached by SWR after that. Until it resolves every dashboard sits in the
     * invited section, which is how the menu behaved before the split.
     */
    const userId = auth?.user?.id;
    const { data: adminOrgIds } = useSWR(
        open && userId && list && list.length > 0
            ? ["organization-admin", userId, list.map((o) => o.id).join(",")]
            : null,
        async () => {
            const ids = await Promise.all(
                (list ?? []).map(async (org) => {
                    try {
                        const members: OrganizationUser[] = await fetcher(
                            `/organizations/${org.id}/users`,
                        );
                        return members.some(
                            (m) => m.id === userId && m.is_admin,
                        )
                            ? org.id
                            : null;
                    } catch {
                        // A membership that cannot be read counts as non-admin
                        // rather than failing the whole menu.
                        return null;
                    }
                }),
            );
            return new Set(ids.filter((id): id is string => id !== null));
        },
        { revalidateOnFocus: false },
    );

    const owned = list?.filter((org) => adminOrgIds?.has(org.id)) ?? [];
    const invited = list?.filter((org) => !adminOrgIds?.has(org.id)) ?? [];

    const refreshOrgList = async () => {
        setOrganizationList(await getOrganizations());
    };

    return (
        <>
            <DropdownMenu open={open} onOpenChange={setOpen}>
                <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
                <DropdownMenuContent
                    side="top"
                    align="start"
                    sideOffset={0}
                    /*
                     * Collision handling stays on so the panel is nudged back
                     * on-screen when the trigger sits near an edge — which it
                     * does on the mobile bottom bar, where Account is the
                     * right-most item. On the desktop rail there is nothing to
                     * collide with, so the Figma placement is unaffected.
                     */
                    collisionPadding={8}
                    className={cn(
                        // Left edge at the trigger's centre, which is the rail's
                        // placement. Not applied on the bottom bar, where it
                        // would push the panel off the right of the screen.
                        "md:ml-[calc(var(--radix-dropdown-menu-trigger-width)/2)]",
                        "flex min-w-0 flex-col overflow-hidden px-0 py-2",
                        "rounded-menu border-2 border-cc-button-hover bg-cc-background",
                        "shadow-menu",
                        // Respect a reduced-motion preference.
                        "motion-reduce:animate-none motion-reduce:transition-none",
                    )}
                >
                    {invited.length > 0 && (
                        <p className="type-menu-heading px-4 py-4 text-center text-cc-white">
                            Dashboards you&apos;ve been invited to
                        </p>
                    )}

                    {invited.map((org) => (
                        <MenuRow
                            key={org.id}
                            isCurrent={org.id === selectedOrg}
                            onSelect={() => onSelectOrg(org.id)}
                            icon={
                                <OrganizationIcon className="size-6 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuRow>
                    ))}

                    {/*
                     * Not present in the Figma frame, but the organization
                     * switcher it replaces owned the only entry point to
                     * creating an organization. Removing it would delete
                     * working functionality, so it is kept here using the
                     * design's own row styling.
                     */}
                    <MenuRow
                        onSelect={() => newOrgModal.open()}
                        icon={<PlusIcon className="size-6 shrink-0" />}
                    >
                        Add new organization
                    </MenuRow>

                    {/* Figma 218:14547 — a rule with 10px of space either side. */}
                    <div className="my-2.5 border-t border-cc-gray" />

                    {/*
                     * The dashboards the user administers — their own. Figma
                     * 218:14548 shows a person's name here. They select like any
                     * other dashboard and highlight when one is being viewed.
                     */}
                    {owned.map((org) => (
                        <MenuRow
                            key={org.id}
                            isCurrent={org.id === selectedOrg}
                            onSelect={() => onSelectOrg(org.id)}
                            icon={
                                <OrganizationIcon className="size-6 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuRow>
                    ))}

                    {/* Figma 218:14549 — sits between the profile row and
                        "Log out", as the design orders them. */}
                    <MenuRow
                        onSelect={() => navigate("/settings")}
                        icon={<SettingsIcon className="size-6 shrink-0" />}
                    >
                        Settings
                    </MenuRow>

                    <MenuRow
                        onSelect={() => {
                            window.location.href = `${import.meta.env.VITE_API_URL}/auth/logout`;
                        }}
                        icon={<ExitToAppIcon className="size-6 shrink-0" />}
                    >
                        Log out
                    </MenuRow>
                </DropdownMenuContent>
            </DropdownMenu>

            <CreateOrganizationModal
                isOpen={newOrgModal.isOpen}
                onClose={newOrgModal.close}
                onOrganizationCreated={refreshOrgList}
            />
        </>
    );
}
