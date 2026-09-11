import { FigmaIconProps } from "./types";

/*
 * Lock icon — a closed padlock, drawn in the same pixel-art style as the rail's
 * icons.
 */

export function LockIcon({ className }: FigmaIconProps) {
    return (
        <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            <path d="m20,12v-1h-2v-6h-1v-2h-1v-1h-2v-1h-4v1h-2v1h-1v2h-1v6h-2v1h-1v10h1v1h16v-1h1v-10h-1Zm-11-7v-1h1v-1h4v1h1v1h1v6h-8v-6h1Zm-4,16v-8h14v8H5Z" />
        </svg>
    );
}
