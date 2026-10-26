import * as React from "react";

import { cn } from "@/helpers/utils";
import { SecondaryButton } from "./secondary-button";

/*
 * An icon-only action: the outlined button, square and sized to its glyph.
 *
 * It renders through `SecondaryButton` rather than restating its treatment, so
 * the hover to #a0c55b and the pressed green stay in one place — this makes it
 * square, drops the text padding, and quiets it at rest. The 2px radius comes
 * with it, which is the radius every other control in the app carries.
 *
 * At rest the glyph is the design's "Gray" (#949494) — the fill it gives secondary
 * icons — inside a #464646 outline, rather than the white a labelled button uses.
 * These sit beside a page heading and are not what the eye should land on first;
 * the hover is what makes them findable.
 *
 * Callers must give it an `aria-label`: there is no text to name it.
 */
type IconButtonProps = React.ComponentPropsWithoutRef<
    typeof SecondaryButton
> & {
    "aria-label": string;
};

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
    ({ className, ...props }, ref) => (
        <SecondaryButton
            ref={ref}
            className={cn(
                "size-10 shrink-0 border-cc-dark-gray p-0 text-cc-gray",
                className,
            )}
            {...props}
        />
    ),
);
IconButton.displayName = "IconButton";
