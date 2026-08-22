import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useSWR from "swr";

import { getOrganizations } from "@/api/organizations";
import { Organization, OrganizationUser, User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { cn } from "@/helpers/utils";
import { useModal } from "@/hooks/useModal";
import CreateOrganizationModal from "./createOrganizationModal";
import { ExitToAppIcon } from "./icons/exit-to-app-icon";
import { SettingsIcon } from "./icons/settings-icon";
import { OrganizationIcon } from "./icons/organization-icon";
import { PlusIcon } from "./icons/plus-icon";
import { DropdownMenu, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { MenuItem, MenuPanel } from "./ui/menu";

/*
 * The account menu, the subject of the design's "Changing organization from side
 * bar".
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
 *   heading Inter Medium 10px, centred, 15px vertical padding
 *   row     46px tall, 15px/8px padding, 4px gap, 24px avatar,
 *           IBM Plex Mono Medium 12px label
 *   rule    1px #949494 with 10px either side
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
    /*
     * Latched on the first open, and never cleared. The admin lookup below is
     * keyed on it rather than on `open` so that closing the menu does not drop the
     * result: with the key gone, SWR reports no data, every dashboard falls back
     * into the "invited" group, and the one the user administers visibly jumps up
     * out of its section while the menu is animating out.
     */
    const [hasOpened, setHasOpened] = useState(false);
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
     * Deferred until the menu is first opened, to keep it off the page-load path,
     * and kept from then on — see `hasOpened`. Until it resolves every dashboard
     * sits in the invited section, which is how the menu behaved before the split.
     */
    const userId = auth?.user?.id;
    const { data: adminOrgIds } = useSWR(
        hasOpened && userId && list && list.length > 0
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
            <DropdownMenu
                open={open}
                onOpenChange={(next) => {
                    setOpen(next);
                    if (next) setHasOpened(true);
                }}
            >
                <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
                <MenuPanel
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
                    )}
                >
                    {invited.length > 0 && (
                        <p className="type-menu-heading px-4 py-4 text-center text-cc-white">
                            Dashboards you&apos;ve been invited to
                        </p>
                    )}

                    {invited.map((org) => (
                        <MenuItem
                            key={org.id}
                            isCurrent={org.id === selectedOrg}
                            onSelect={() => onSelectOrg(org.id)}
                            icon={
                                <OrganizationIcon className="size-6 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuItem>
                    ))}

                    {/*
                     * Not present in the Figma frame, but the organization
                     * switcher it replaces owned the only entry point to
                     * creating an organization. Removing it would delete
                     * working functionality, so it is kept here using the
                     * design's own row styling.
                     */}
                    <MenuItem
                        onSelect={() => newOrgModal.open()}
                        icon={<PlusIcon className="size-6 shrink-0" />}
                    >
                        Add new organization
                    </MenuItem>

                    {/* A rule with 10px of space either side. */}
                    <div className="my-2.5 border-t border-cc-gray" />

                    {/*
                     * The dashboards the user administers — their own. Figma
                     * The design shows a person's name here. They select like any
                     * other dashboard and highlight when one is being viewed.
                     */}
                    {owned.map((org) => (
                        <MenuItem
                            key={org.id}
                            isCurrent={org.id === selectedOrg}
                            onSelect={() => onSelectOrg(org.id)}
                            icon={
                                <OrganizationIcon className="size-6 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuItem>
                    ))}

                    {/* Sits between the profile row and
                        "Log out", as the design orders them. */}
                    <MenuItem
                        onSelect={() => navigate("/settings")}
                        icon={<SettingsIcon className="size-6 shrink-0" />}
                    >
                        Settings
                    </MenuItem>

                    <MenuItem
                        onSelect={() => {
                            window.location.href = `${import.meta.env.VITE_API_URL}/auth/logout`;
                        }}
                        icon={<ExitToAppIcon className="size-6 shrink-0" />}
                    >
                        Log out
                    </MenuItem>
                </MenuPanel>
            </DropdownMenu>

            <CreateOrganizationModal
                isOpen={newOrgModal.isOpen}
                onClose={newOrgModal.close}
                onOrganizationCreated={refreshOrgList}
            />
        </>
    );
}
