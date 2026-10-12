import { Organization } from "@/api/schemas";
import { SelectGroup } from "@radix-ui/react-select";
import {
    AreaChart,
    Building,
    Home,
    LogOutIcon,
    UserIcon,
    Users,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import NavItem from "./nav-item";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "./ui/select";
import CreateOrganizationModal from "./createOrganizationModal";
import { getOrganizations } from "@/api/organizations";
import { Button } from "./ui/button";
import { useModal } from "@/hooks/useModal";

const USER_PROFILE_URL = import.meta.env.VITE_OIDC_PROFILE_URL;
export default function NavBar({
    orgs,
    setSheetOpened,
}: Readonly<{
    orgs: Organization[] | undefined;
    setSheetOpened?: (value: boolean) => void;
}>) {
    const [selected, setSelected] = useState<string | null>(null);
    const navigate = useNavigate();
    const [selectedOrg, setSelectedOrg] = useState<string | null>(() => {
        try {
            return localStorage.getItem("organizationId");
        } catch {
            return null;
        }
    });
    const iconStyles = "h-4 w-4 flex-shrink-0 text-muted-foreground";
    const { pathname } = useLocation();
    const newOrgModal = useModal();
    const [organizationList, setOrganizationList] = useState<
        Organization[] | undefined
    >([]);
    const [isDropdownOpen, setDropdownOpen] = useState(false);

    useEffect(() => {
        if (pathname.includes("/members")) {
            setSelected("members");
        } else if (pathname.includes("/profile")) {
            setSelected("profile");
        } else if (pathname.includes("/projects")) {
            setSelected("projects");
            return;
        } else {
            setSelected("home");
        }
    }, [pathname, orgs]);

    useEffect(() => {
        if (orgs) {
            setOrganizationList(orgs);
        }
    }, [orgs]);

    useEffect(() => {
        if (!organizationList?.length) {
            setSelectedOrg(null);
            return;
        }
        const routeOrgId = pathname.split("/")[1];
        if (organizationList.some((org) => org.id === routeOrgId)) {
            setSelectedOrg(routeOrgId);
        } else if (!organizationList.some((org) => org.id === selectedOrg)) {
            setSelectedOrg(organizationList[0].id);
        }
    }, [pathname, organizationList, selectedOrg]);

    useEffect(() => {
        if (!selectedOrg) return;
        try {
            localStorage.setItem("organizationId", selectedOrg);
            const organizationName = organizationList?.find(
                (organization) => organization.id === selectedOrg,
            )?.name;
            if (organizationName) {
                localStorage.setItem("organizationName", organizationName);
            }
        } catch (error) {
            console.error("Error writing to localStorage:", error);
        }
    }, [selectedOrg, organizationList]);

    const handleNewOrgClick = async () => {
        newOrgModal.open();
        setDropdownOpen(false); // Close the dropdown menu
    };

    const refreshOrgList = async () => {
        // Fetch the updated list of organizations from the server
        const orgs = await getOrganizations();
        setOrganizationList(orgs);
    };

    return (
        <div className="flex-1 p-8">
            <nav className="flex flex-col h-full font-medium text-sm text-muted-foreground">
                <div className="flex-1">
                    <div className="flex flex-col gap-2 py-4">
                        <NavItem
                            isSelected={selected === "home"}
                            onClick={() => {
                                setSelected("home");
                                setSheetOpened?.(false);

                                if (selectedOrg) {
                                    navigate(`/${selectedOrg}`);
                                } else {
                                    navigate("/home");
                                }
                            }}
                            paddingY={1.5}
                            icon={<Home className={iconStyles} />}
                        >
                            Home
                        </NavItem>

                        <>
                            <NavItem
                                isSelected={selected === "projects"}
                                onClick={() => {
                                    if (!selectedOrg) return;
                                    setSelected("projects");
                                    setSheetOpened?.(false);
                                    navigate(`/${selectedOrg}/projects`);
                                }}
                                paddingY={1.5}
                                icon={<AreaChart className={iconStyles} />}
                            >
                                Projects
                            </NavItem>
                            <NavItem
                                isSelected={selected === "members"}
                                onClick={() => {
                                    if (!selectedOrg) return;
                                    setSelected("members");
                                    setSheetOpened?.(false);
                                    navigate(`/${selectedOrg}/members`);
                                }}
                                paddingY={1.5}
                                icon={<Users className={iconStyles} />}
                            >
                                Members
                            </NavItem>
                        </>
                    </div>
                </div>
                <div className="mt-auto">
                    <div className="flex flex-col gap-2">
                        {selectedOrg && (
                            <Select
                                value={selectedOrg}
                                onValueChange={(value) => {
                                    setSelectedOrg(value);
                                    setSelected("home");
                                    setSheetOpened?.(false);
                                    navigate(`/${value}`);
                                }}
                                open={isDropdownOpen}
                                onOpenChange={setDropdownOpen}
                            >
                                <SelectTrigger
                                    className="flex items-center gap-2 [&>span]:line-clamp-1 [&>span]:flex [&>span]:w-full [&>span]:items-center [&>span]:gap-1 [&>span]:truncate [&_svg]:h-4 [&_svg]:w-4 [&_svg]:shrink-0"
                                    aria-label="Select account"
                                >
                                    <SelectValue placeholder="Select an organization">
                                        <Building className={iconStyles} />
                                        <span className="ml-2 truncate">
                                            {(organizationList &&
                                                organizationList.find(
                                                    (org) =>
                                                        org.id === selectedOrg,
                                                )?.name) ||
                                                selectedOrg}
                                        </span>
                                    </SelectValue>
                                </SelectTrigger>
                                <SelectContent>
                                    <Button
                                        onClick={handleNewOrgClick}
                                        variant="ghost"
                                    >
                                        + Add new organization
                                    </Button>
                                    <SelectGroup>
                                        <SelectLabel className="text-sm font-medium text-muted-foreground">
                                            Organizations
                                        </SelectLabel>
                                        {organizationList &&
                                            organizationList.map((org) => (
                                                <SelectItem
                                                    key={org.id}
                                                    value={org.id}
                                                >
                                                    <div className="flex items-center gap-3 [&_svg]:h-4 [&_svg]:w-4 [&_svg]:shrink-0 [&_svg]:text-foreground">
                                                        {org.name}
                                                    </div>
                                                </SelectItem>
                                            ))}
                                    </SelectGroup>
                                </SelectContent>
                            </Select>
                        )}
                        <CreateOrganizationModal
                            isOpen={newOrgModal.isOpen}
                            onClose={newOrgModal.close}
                            onOrganizationCreated={refreshOrgList}
                        />
                        {USER_PROFILE_URL && (
                            <NavItem
                                isSelected={selected === "profile"}
                                onClick={() => {
                                    setSelected("profile");
                                    setSheetOpened?.(false);
                                    window.location.href = USER_PROFILE_URL!; // Redirect to the OIDC provider's profile page to handle profile updates there
                                }}
                                paddingY={1.5}
                                icon={<UserIcon className={iconStyles} />}
                            >
                                Profile
                            </NavItem>
                        )}
                        <NavItem
                            onClick={() => {
                                setSheetOpened?.(false);
                                window.location.href = `${import.meta.env.VITE_API_URL}/auth/logout`;
                            }}
                            isSelected={false}
                            paddingY={1.5}
                            icon={<LogOutIcon className={iconStyles} />}
                        >
                            Log out
                        </NavItem>
                    </div>
                </div>
            </nav>
        </div>
    );
}
