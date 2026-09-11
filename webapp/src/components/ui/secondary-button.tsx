import * as React from "react";

import { cn } from "@/helpers/utils";

/*
 * The outlined counterpart to `PrimaryButton`, for an action that sits beside a
 * form rather than completing it.
 *
 * The design has no frame for one, so it is built from the palette the redesign
 * already uses: the field's own border weight and radius, white text on nothing,
 * and the same `Button-hover` (#a0c55b) that every other control in the app moves
 * to — so it reads as the quieter sibling of the lime button rather than as a
 * different kind of control. It carries the same `ringOffset` choice for the same
 * reason.
 */
type SecondaryButtonProps = React.ComponentPropsWithoutRef<"button"> & {
    ringOffset?: "background" | "page";
};

export const SecondaryButton = React.forwardRef<
    HTMLButtonElement,
    SecondaryButtonProps
>(
    (
        { className, type = "button", ringOffset = "background", ...props },
        ref,
    ) => (
        <button
            ref={ref}
            type={type}
            className={cn(
                "type-mono-regular type-field inline-flex cursor-pointer items-center justify-center gap-2",
                "rounded-field border border-cc-gray bg-transparent px-4 py-2 text-cc-white outline-none transition",
                "hover:border-cc-button-hover hover:text-cc-button-hover",
                "active:border-cc-lime active:text-cc-lime",
                "focus-visible:ring-2 focus-visible:ring-cc-lime focus-visible:ring-offset-2",
                ringOffset === "page"
                    ? "focus-visible:ring-offset-cc-page-background"
                    : "focus-visible:ring-offset-cc-background",
                "disabled:cursor-not-allowed disabled:opacity-50",
                "motion-reduce:transition-none",
                className,
            )}
            {...props}
        />
    ),
);
SecondaryButton.displayName = "SecondaryButton";
