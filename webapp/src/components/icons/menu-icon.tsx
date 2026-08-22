import { FigmaIconProps } from "./types";

/*
 * Menu icon — three bars stacked one above another.
 */

export function MenuIcon({ className }: FigmaIconProps) {
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
            <path d="M3 18V16H21V18H3ZM3 13V11H21V13H3ZM3 8V6H21V8H3Z" />
        </svg>
    );
}
