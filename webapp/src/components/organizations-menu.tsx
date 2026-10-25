import { useState } from "react";

import { getOrganizations } from "@/api/organizations";
import { Organization } from "@/api/schemas";
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
    const newOrgModal = useModal();
    const [organizationList, setOrganizationList] = useState<
        Organization[] | undefined
    >(undefined);

    const list = organizationList ?? orgs;

    // Dashboards the user administers go below the rule.
    const owned = list?.filter((org) => org.is_admin) ?? [];
    const invited = list?.filter((org) => !org.is_admin) ?? [];

    const refreshOrgList = async () => {
        setOrganizationList(await getOrganizations());
    };

    return (
        <>
            <DropdownMenu>
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
