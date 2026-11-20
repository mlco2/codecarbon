import { FigmaIconProps } from "./types";

/*
 * Share icon — three nodes joined by lines, drawn in the same pixel-art style as
 * the rail's icons.
 */

export function ShareIcon({ className }: FigmaIconProps) {
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
            <path d="m20,9v-1h1v-2h1v-2h-1v-2h-1v-1h-5v1h-1v2h-1v2h-1v1h-1v1h-1v1h-1v-1h-5v1h-1v2h-1v2h1v2h1v1h5v-1h1v1h1v1h1v1h1v2h1v2h1v1h5v-1h1v-2h1v-2h-1v-2h-1v-1h-5v1h-2v-1h-1v-1h-1v-4h1v-1h1v-1h2v1h5Zm-11,4h-1v1h-3v-1h-1v-2h1v-1h3v1h1v2Zm6,5h1v-1h3v1h1v2h-1v1h-3v-1h-1v-2Zm0-14h1v-1h3v1h1v2h-1v1h-3v-1h-1v-2Z" />
        </svg>
    );
}
