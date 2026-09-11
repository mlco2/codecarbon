"use client";

import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";

import { cn } from "@/helpers/utils";

/*
 * The redesign's toggle: square-cornered like the buttons, with a matching
 * square thumb, green when on.
 *
 * The design has no frame for a switch, so this is built from the vocabulary it
 * does define — the 2px radius its fields and buttons carry, the lime that marks
 * anything active, and the #a0c55b every control in the app moves to on hover.
 * The thumb takes the page's own dark fill, so it reads as a hole punched in the
 * track rather than a chip sitting on top of it.
 *
 * Restyled in place rather than added alongside the shadcn switch: this is the
 * app's only switch, so a second one would leave the original with no callers.
 */
const Switch = React.forwardRef<
    React.ElementRef<typeof SwitchPrimitives.Root>,
    React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
    <SwitchPrimitives.Root
        className={cn(
            "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center",
            "rounded-field border-2 border-transparent transition-colors",
            "data-[state=unchecked]:bg-white/12 data-[state=checked]:bg-cc-lime",
            "hover:data-[state=checked]:bg-cc-button-hover hover:data-[state=unchecked]:bg-white/20",
            "outline-none focus-visible:ring-2 focus-visible:ring-cc-lime focus-visible:ring-offset-2 focus-visible:ring-offset-cc-background",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "motion-reduce:transition-none",
            className,
        )}
        {...props}
        ref={ref}
    >
        <SwitchPrimitives.Thumb
            className={cn(
                "pointer-events-none block size-5 rounded-field ring-0 transition-transform",
                "data-[state=unchecked]:bg-cc-gray data-[state=checked]:bg-cc-background",
                "data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0",
                "motion-reduce:transition-none",
            )}
        />
    </SwitchPrimitives.Root>
));
Switch.displayName = SwitchPrimitives.Root.displayName;

export { Switch };
