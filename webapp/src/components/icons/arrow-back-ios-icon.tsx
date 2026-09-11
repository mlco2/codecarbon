import { FigmaIconProps } from "./types";

/*
 * Back icon — a chevron pointing left.
 */

export function ArrowBackIosIcon({ className }: FigmaIconProps) {
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
            <g transform="translate(0.346 2.346)">
                <path d="M9.65375 19.3075L0 9.65375L9.65375 0L11.073 1.41925L2.83825 9.65375L11.073 17.8883L9.65375 19.3075Z" />
            </g>
        </svg>
    );
}
