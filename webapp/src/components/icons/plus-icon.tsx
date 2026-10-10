import { FigmaIconProps } from "./types";

/*
 * Plus icon — a plus sign.
 */

export function PlusIcon({ className }: FigmaIconProps) {
    return (
        <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            <path
                fill="currentColor"
                d="M19 12.998h-6v6h-2v-6H5v-2h6v-6h2v6h6z"
            />
        </svg>
    );
}
