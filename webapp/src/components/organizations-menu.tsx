import { useState } from "react";
import useSWR from "swr";

import { getOrganizations } from "@/api/organizations";
import { Organization, OrganizationUser, User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { useModal } from "@/hooks/useModal";
import CreateOrganizationModal from "./create-organization-modal";
import { OrganizationIcon } from "./icons/organization-icon";
import { PlusIcon } from "./icons/plus-icon";
import { DropdownMenu, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { MenuItem, MenuPanel } from "./ui/menu";

export default function OrganizationsMenu({
    orgs,
    selectedOrg,
    onSelectOrg,
    children,
}: Readonly<{
    orgs: Organization[] | undefined;
    selectedOrg: string | null;
    onSelectOrg: (organizationId: string) => void;
    /** The rail's "Organizations" item, used as the trigger. */
    children: React.ReactNode;
}>) {
    const [open, setOpen] = useState(false);
    // Keyed on instead of `open`, so closing the menu does not drop the admin
    // lookup below and regroup the organizations as it animates out.
    const [hasOpened, setHasOpened] = useState(false);
    const newOrgModal = useModal();
    const [organizationList, setOrganizationList] = useState<
        Organization[] | undefined
    >(undefined);

    const { data: auth } = useSWR<{ user?: User }>("/auth/check", fetcher, {
        revalidateOnFocus: false,
    });

    const list = organizationList ?? orgs;

    // Admin rights are exposed only per organization, on its member list, so
    // this asks each in turn. Dashboards the user administers go below the rule.
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
                {/* Opens beside the rail, bottom edges level with the trigger. The offset
                crosses the rail's 16px padding and 2px border, plus an 8px gap. */}
                <MenuPanel
                    side="right"
                    align="end"
                    sideOffset={26}
                    collisionPadding={8}
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
                                <OrganizationIcon className="-mx-0.5 size-6 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuItem>
                    ))}

                    <MenuItem
                        onSelect={() => newOrgModal.open()}
                        icon={<PlusIcon className="-mx-0.5 size-6 shrink-0" />}
                    >
                        Add new organization
                    </MenuItem>

                    {owned.length > 0 && (
                        <div className="my-2.5 border-t border-cc-gray" />
                    )}

                    {owned.map((org) => (
                        <MenuItem
                            key={org.id}
                            isCurrent={org.id === selectedOrg}
                            onSelect={() => onSelectOrg(org.id)}
                            icon={
                                <OrganizationIcon className="-mx-0.5 size-7 shrink-0" />
                            }
                        >
                            {org.name}
                        </MenuItem>
                    ))}
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
