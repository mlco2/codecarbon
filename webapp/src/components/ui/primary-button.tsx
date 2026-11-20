import * as React from "react";

import { cn } from "@/helpers/utils";

/*
 * The redesign's primary action: the lime button, wherever the design calls for
 * one.
 *
 * Separate from `ui/button.tsx` rather than added to it as a variant — that
 * button's variants are built on the shadcn token set (`bg-primary`,
 * `ring-offset-background`) and every screen the redesign has not reached still
 * renders them, so its shape is not free to change. This one owns the design's
 * treatment and nothing else renders through it by accident.
 *
 * `ringOffset` exists because the focus ring is drawn against whatever the button
 * sits on: the page's surface behind a page-level action, the panel's behind one
 * in a dialog. It is the only thing about the button that its context decides.
 */
type PrimaryButtonProps = React.ComponentPropsWithoutRef<"button"> & {
    ringOffset?: "background" | "page";
};

export const PrimaryButton = React.forwardRef<
    HTMLButtonElement,
    PrimaryButtonProps
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
                "rounded-field bg-cc-lime px-6 py-2 text-cc-background outline-none transition",
                "hover:bg-cc-button-hover active:bg-cc-button-hover active:brightness-90",
                "focus-visible:ring-2 focus-visible:ring-cc-white focus-visible:ring-offset-2",
                ringOffset === "page"
                    ? "focus-visible:ring-offset-cc-page-background"
                    : "focus-visible:ring-offset-cc-background",
                "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-cc-lime disabled:active:brightness-100",
                "motion-reduce:transition-none",
                className,
            )}
            {...props}
        />
    ),
);
PrimaryButton.displayName = "PrimaryButton";
