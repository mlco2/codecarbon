import { redirectToAccount, redirectToLogout } from "@/api/auth";
import { LogoutIcon } from "./icons/logout-icon";
import { SettingsIcon } from "./icons/settings-icon";
import { DropdownMenu, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { MenuItem, MenuPanel } from "./ui/menu";

export default function AccountMenu({
    children,
}: Readonly<{
    /** The rail's "Account" item, used as the trigger. */
    children: React.ReactNode;
}>) {
    return (
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
                {/* Email and password are owned by the identity provider,
                    so this leaves the app for its account console. The API
                    holds the issuer URL and redirects, the same way login
                    does. */}
                <MenuItem
                    onSelect={redirectToAccount}
                    icon={<SettingsIcon className="size-6 shrink-0" />}
                >
                    Settings
                </MenuItem>

                <MenuItem
                    onSelect={redirectToLogout}
                    icon={
                        <LogoutIcon className="size-5 shrink-0 translate-x-1" />
                    }
                >
                    Log out
                </MenuItem>
            </MenuPanel>
        </DropdownMenu>
    );
}
