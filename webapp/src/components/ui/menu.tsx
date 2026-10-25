import * as React from "react";

import { cn } from "@/helpers/utils";
import {
    DropdownMenuContent,
    DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

/*
 * The redesign's dropdown menu: a dark panel with a green edge, and rows that
 * highlight as one.
 *
 * Both menus in the app — the account menu at the end of the rail, and a project
 * row's overflow menu — are the same object in the design, so they render through
 * these rather than each restating the panel's border, fill and shadow.
 *
 * The design defines a single highlight treatment and does not distinguish hover
 * from selected, so `isCurrent` and the hover/focus state share it: a #2b2b2b
 * fill with a green right edge and a green label. Focus is bound as well as hover
 * so the menu is fully operable from the keyboard — Radix moves focus with the
 * arrow keys and also sets it on hover.
 */

export const MenuPanel = React.forwardRef<
    React.ElementRef<typeof DropdownMenuContent>,
    React.ComponentPropsWithoutRef<typeof DropdownMenuContent>
>(({ className, ...props }, ref) => (
    <DropdownMenuContent
        ref={ref}
        className={cn(
            "flex min-w-0 flex-col overflow-hidden px-0 py-2",
            "rounded-menu border-2 border-cc-button-hover bg-cc-background shadow-menu",
            "motion-reduce:animate-none motion-reduce:transition-none",
            className,
        )}
        {...props}
    />
));
MenuPanel.displayName = "MenuPanel";

type MenuItemProps = React.ComponentPropsWithoutRef<typeof DropdownMenuItem> & {
    /** Rendered before the label, at the row's own size. */
    icon?: React.ReactNode;
    /** Marks the row as the thing currently being viewed. */
    isCurrent?: boolean;
};

export const MenuItem = React.forwardRef<
    React.ElementRef<typeof DropdownMenuItem>,
    MenuItemProps
>(({ className, children, icon, isCurrent, ...props }, ref) => (
    <DropdownMenuItem
        ref={ref}
        aria-current={isCurrent ? "true" : undefined}
        className={cn(
            "group min-h-control w-full cursor-pointer select-none items-center gap-3 rounded-none px-4 py-2 outline-none",
            // Only the icons take this; the label sets its own colour below.
            "border-y-0 border-l-0 border-r-0 border-transparent text-cc-gray",
            "focus:border-cc-button-hover focus:bg-cc-darkest-gray focus:text-cc-button-hover",
            "data-[highlighted]:border-cc-button-hover data-[highlighted]:bg-cc-darkest-gray data-[highlighted]:text-cc-button-hover",
            isCurrent &&
                "border-cc-button-hover bg-cc-darkest-gray text-cc-button-hover",
            className,
        )}
        {...props}
    >
        {icon}
        {/* Fills the remaining width rather than sitting in a fixed text box, so
            a long name wraps instead of overflowing. */}
        <span
            className={cn(
                "type-mono-medium type-menu-item min-w-0 flex-1 break-words",
                "group-focus:text-cc-button-hover group-data-[highlighted]:text-cc-button-hover",
                isCurrent ? "text-cc-button-hover" : "text-cc-white",
            )}
        >
            {children}
        </span>
    </DropdownMenuItem>
));
MenuItem.displayName = "MenuItem";
