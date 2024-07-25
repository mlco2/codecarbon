"use client";

import { cn } from "@/helpers/utils";
import { Organization } from "@/types/organization";
import { SelectGroup } from "@radix-ui/react-select";
import {
    AreaChart,
    Building,
    Home,
    LogOutIcon,
    UserIcon,
    Users,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
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

export default function NavBar({
    orgs,
}: Readonly<{
    orgs: Organization[] | undefined;
}>) {
    const [selected, setSelected] = useState<string | null>(null);
    const router = useRouter();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
    const iconStyles = "h-4 w-4 flex-shrink-0 text-muted-foreground";
    const pathname = usePathname();

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
        if (!selectedOrg) {
            try {
                const localOrg = localStorage.getItem("organizationId");
                if (localOrg) {
                    setSelectedOrg(localOrg);
                } else if (orgs && orgs.length > 0) {
                    // Set the first organization as the default
                    setSelectedOrg(orgs[0].id);
                }
            } catch (error) {
                console.error("Error reading from localStorage:", error);
            }
        }
    }, [selectedOrg, orgs]); // Empty dependency array, runs only on mount

    // Effect for updating localStorage when selectedOrg changes
    useEffect(() => {
        if (selectedOrg) {
            try {
                const localOrg = localStorage.getItem("organizationId");
                if (localOrg !== selectedOrg) {
                    localStorage.setItem("organizationId", selectedOrg);
                }
            } catch (error) {
                console.error("Error writing to localStorage:", error);
            }
        }
    }, [selectedOrg]);

    return (
        <div className="flex-1 p-8">
            <nav className="flex flex-col h-full font-medium text-sm text-muted-foreground">
                <div className="flex-1">
                    <div className="flex flex-col gap-2 py-4">
                        <NavItem
                            isSelected={selected === "home"}
                            onClick={() => {
                                setSelected("home");
                                if (selectedOrg) {
                                    router.push(`/${selectedOrg}`);
                                } else {
                                    router.push("/home");
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
                                    setSelected("projects");
                                    router.push(`/${selectedOrg}/projects`);
                                }}
                                paddingY={1.5}
                                icon={<AreaChart className={iconStyles} />}
                            >
                                Projects
                            </NavItem>
                            <NavItem
                                isSelected={selected === "members"}
                                onClick={() => {
                                    setSelected("members");
                                    router.push(`/${selectedOrg}/members`);
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
                                defaultValue={selectedOrg}
                                onValueChange={(value) => {
                                    setSelectedOrg(value);
                                    setSelected("home");
                                    router.push(`/${value}`);
                                }}
                            >
                                <SelectTrigger
                                    className={cn(
                                        "flex items-center gap-2 [&>span]:line-clamp-1 [&>span]:flex [&>span]:w-full [&>span]:items-center [&>span]:gap-1 [&>span]:truncate [&_svg]:h-4 [&_svg]:w-4 [&_svg]:shrink-0",
                                        isCollapsed &&
                                            "flex h-9 w-9 shrink-0 items-center justify-center p-0 [&>span]:w-auto [&>svg]:hidden"
                                    )}
                                    aria-label="Select account"
                                >
                                    <SelectValue placeholder="Select an organization">
                                        <Building className={iconStyles} />
                                        <span
                                            className={cn(
                                                "ml-2 truncate",
                                                isCollapsed && "hidden"
                                            )}
                                        >
                                            {orgs &&
                                                orgs.find(
                                                    (org) =>
                                                        org.id === selectedOrg
                                                )?.name}
                                        </span>
                                    </SelectValue>
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectGroup>
                                        <SelectLabel className="text-sm font-medium text-muted-foreground">
                                            Organizations
                                        </SelectLabel>
                                        {orgs &&
                                            orgs.map((org) => (
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
                        <NavItem
                            isSelected={selected === "profile"}
                            onClick={() => {
                                setSelected("profile");
                                router.push(`/profile`);
                            }}
                            paddingY={1.5}
                            icon={<UserIcon className={iconStyles} />}
                        >
                            Profile
                        </NavItem>
                        <NavItem
                            onClick={() => {
                                router.push("/logout");
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
