import * as React from "react";

import { cn } from "@/helpers/utils";
import { TabsList, TabsTrigger } from "@/components/ui/tabs";

/*
 * Tabs in the redesign's own vocabulary: a rule under the row, labels in the
 * display face, green when selected and dimmed white when not — the treatment the
 * Settings page uses for its sub-navigation, applied to Radix tabs.
 *
 * The selected tab carries a 2px green underline that sits on the list's rule
 * rather than below it, and the row is tall enough that the labels have air around
 * them instead of sitting tight against that line.
 *
 * These wrap the shadcn tab primitives instead of replacing them, so the
 * keyboard behaviour and roles are untouched and only the appearance changes.
 */

export const TabNavList = React.forwardRef<
    React.ElementRef<typeof TabsList>,
    React.ComponentPropsWithoutRef<typeof TabsList>
>(({ className, ...props }, ref) => (
    <TabsList
        ref={ref}
        className={cn(
            "h-auto w-full justify-start gap-8 rounded-none border-b border-cc-rule bg-transparent p-0",
            className,
        )}
        {...props}
    />
));
TabNavList.displayName = "TabNavList";

export const TabNavTrigger = React.forwardRef<
    React.ElementRef<typeof TabsTrigger>,
    React.ComponentPropsWithoutRef<typeof TabsTrigger>
>(({ className, ...props }, ref) => (
    <TabsTrigger
        ref={ref}
        className={cn(
            "type-display type-settings-nav cursor-pointer rounded-none bg-transparent px-0 pb-2.5 pt-4",
            "text-cc-white/50 shadow-none outline-none transition-colors hover:text-cc-button-hover",
            // The selected tab is underlined by its own bottom edge, pulled down
            // over the list's rule so the two read as one line rather than
            // stacking. 2px, the same weight as every other edge in the design.
            "-mb-px border-x-0 border-b-2 border-t-0 border-transparent",
            "data-[state=active]:border-cc-lime data-[state=active]:bg-transparent data-[state=active]:text-cc-lime data-[state=active]:shadow-none",
            "focus-visible:ring-2 focus-visible:ring-cc-lime motion-reduce:transition-none",
            className,
        )}
        {...props}
    />
));
TabNavTrigger.displayName = "TabNavTrigger";
