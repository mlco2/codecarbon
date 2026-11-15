import { FigmaIconProps } from "./types";

/*
 * Vertical more icon — three dots in a vertical line, pixel-art style.
 */

export function MoreVertIcon({ className }: FigmaIconProps) {
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
            <path d="M14,5l0,2l-1,0l0,1l-2,0l0,-1l-1,0l0,-2l1,0l0,-1l2,0l0,1l1,0Zm0,6l0,2l-1,0l0,1l-2,0l0,-1l-1,0l0,-2l1,0l0,-1l2,0l0,1l1,0Zm0,6l0,2l-1,0l0,1l-2,0l0,-1l-1,0l0,-2l1,0l0,-1l2,0l0,1l1,0Z" />
        </svg>
    );
}
