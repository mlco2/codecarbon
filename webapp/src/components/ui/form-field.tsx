import * as React from "react";

import { cn } from "@/helpers/utils";

/*
 * A labelled text field, as the design draws it: a 16px label, then a 46px
 * control on a 5% white fill with a 2px radius and a #666 placeholder.
 *
 * The label and the control are one component because the design treats them as
 * one — the 4px between them and the label's type are part of the field, not
 * decisions a form remakes each time it needs one. `id` is required for the same
 * reason: the label is only a label if it points at something.
 *
 * Separate from `ui/input.tsx`, which is the shadcn input the screens outside the
 * redesign still use, and which carries no label.
 */
type FormFieldProps = Omit<React.ComponentPropsWithoutRef<"input">, "id"> & {
    id: string;
    label: string;
    /**
     * Hides the label visually while leaving it for assistive technology, for the
     * rare field whose surroundings already name it.
     */
    hideLabel?: boolean;
    /** Classes for the wrapper; `className` styles the control itself. */
    containerClassName?: string;
};

export const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
    (
        {
            id,
            label,
            className,
            containerClassName,
            hideLabel = false,
            type = "text",
            ...props
        },
        ref,
    ) => (
        <div className={cn("flex flex-col gap-1", containerClassName)}>
            <label
                htmlFor={id}
                className={cn(
                    "type-mono-regular type-field text-cc-white",
                    hideLabel && "sr-only",
                )}
            >
                {label}
            </label>
            <input
                ref={ref}
                id={id}
                type={type}
                className={cn(
                    "type-mono-regular type-field h-control w-full rounded-field bg-white/5 px-4",
                    "text-cc-white outline-none placeholder:text-cc-text-input-gray",
                    "focus-visible:ring-2 focus-visible:ring-cc-lime",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    className,
                )}
                {...props}
            />
        </div>
    ),
);
FormField.displayName = "FormField";
