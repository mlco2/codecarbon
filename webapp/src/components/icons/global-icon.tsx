import { FigmaIconProps } from "./types";

/*
 * Global icon — a globe, drawn in the same pixel-art style as the rail's other
 * icons.
 */

export function GlobalIcon({ className }: FigmaIconProps) {
    return (
        <svg
            viewBox="0 0 32 32"
            width="32"
            height="32"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            <path d="M22.85 7.62V10.67H21.33V15.24H22.85V16.76H24.38V18.29H19.81V19.81H18.28V21.33H22.85V24.38H21.33V27.43H22.85V28.95H25.9V27.43H27.43V25.9H28.95V22.86H30.47V19.81H32V12.19H30.47V9.14H28.95V6.1H27.43V7.62H22.85Z" />
            <path d="M27.43 4.57H25.9V6.1H27.43V4.57Z" />
            <path d="M25.9 3.05H22.85V4.57H25.9V3.05Z" />
            <path d="M22.85 28.95H19.81V30.48H22.85V28.95Z" />
            <path d="M22.85 1.52H19.81V3.05H22.85V1.52Z" />
            <path d="M16.76 28.95H15.24V27.43H10.66V28.95H9.14V30.48H12.19V32H19.81V30.48H16.76V28.95Z" />
            <path d="M19.81 0H12.19V1.52H19.81V0Z" />
            <path d="M10.66 16.76H12.19V18.29H13.71V13.71H10.66V16.76Z" />
            <path d="M9.14 27.43H6.09V28.95H9.14V27.43Z" />
            <path d="M6.09 25.9H4.57V27.43H6.09V25.9Z" />
            <path d="M3.05 22.86V25.9H4.57V24.38H6.09V22.86H7.62V18.29H6.09V16.76H4.57V15.24H3.05V13.71H4.57V12.19H9.14V10.67H10.66V9.14H12.19V10.67H13.71V9.14H15.24V6.1H13.71V4.57H10.66V3.05H12.19V1.52H9.14V3.05H6.09V4.57H4.57V6.1H3.05V9.14H1.52V12.19H0V19.81H1.52V22.86H3.05Z" />
        </svg>
    );
}
