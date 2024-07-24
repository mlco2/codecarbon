"use client";

import { cn } from "@/lib/utils";
import { Organization } from "@/types/organization";
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
import { SelectGroup } from "@radix-ui/react-select";

export default function NavBar({
  orgs,
}: Readonly<{
  orgs: Organization[];
}>) {
  const router = useRouter();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const iconStyles = "h-4 w-4 flex-shrink-0 text-muted-foreground";
  const pathname = usePathname();

  useEffect(() => {
    if (!selectedOrg) {
      try {
        const localOrg = localStorage.getItem("organizationId");
        if (localOrg) {
          setSelectedOrg(localOrg);
        }
      } catch (error) {
        console.error("Error reading from localStorage:", error);
      }
    }
  }, [selectedOrg]); // Empty dependency array, runs only on mount

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

  let isHome = pathname === "/home";
  const isProjectSettings =
    pathname.includes("/settings") && pathname.includes("/projects");
  const isProjects = pathname.includes("/projects") && !isProjectSettings;
  const isOrgSettings = pathname.includes("/settings") && !isProjectSettings;

  // Detect if current path is "/<one of the orgs id>"
  if (!isHome) {
    orgs.forEach((org) => {
      if (pathname === `/${org.id}`) {
        isHome = true;
      }
    });
  }

  return (
    <div className="flex-1 p-8">
      <nav className="flex flex-col h-full font-medium text-sm text-muted-foreground">
        <div className="flex-1">
          <div className="flex flex-col gap-2 py-4">
            <NavItem
              isSelected={isHome}
              paddingY={1.5}
              href="/home"
              icon={<Home className={iconStyles} />}
            >
              Home
            </NavItem>
            <NavItem
              href={`/${selectedOrg}/projects`}
              isSelected={isProjects}
              paddingY={1.5}
              icon={<AreaChart className={iconStyles} />}
            >
              Projects
            </NavItem>
            <NavItem
              href={`/${selectedOrg}/members`}
              isSelected={pathname.includes("/members")}
              paddingY={1.5}
              icon={<Users className={iconStyles} />}
            >
              Members
            </NavItem>
          </div>
        </div>
        <div className="mt-auto">
          <div className="flex flex-col gap-2">
            {selectedOrg && (
              <Select
                defaultValue={selectedOrg}
                onValueChange={(value) => {
                  setSelectedOrg(value);
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
                      className={cn("ml-2 truncate", isCollapsed && "hidden")}
                    >
                      {orgs.find((org) => org.id === selectedOrg)?.name}
                    </span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel className="text-sm font-medium text-muted-foreground">
                      Organizations
                    </SelectLabel>
                    {orgs.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
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
              href="/profile"
              isSelected={pathname === "/profile"}
              paddingY={1.5}
              icon={<UserIcon className={iconStyles} />}
            >
              Profile
            </NavItem>
            <NavItem
              href="/logout"
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
