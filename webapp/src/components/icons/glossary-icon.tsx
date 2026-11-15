import { FigmaIconProps } from "./types";

/*
 * Glossary icon — an org chart with a smiling robot at the top branching down
 * to three nodes, drawn in the same pixel-art style as the rail's other icons.
 */

export function GlossaryIcon({ className }: FigmaIconProps) {
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
            <path d="M30.47 24.38H28.95V21.33H27.42V24.38H25.9V25.9H24.38V30.48H25.9V32H30.47V30.48H32V25.9H30.47V24.38Z" />
            <path d="M27.42 19.81H25.9V21.33H27.42V19.81Z" />
            <path d="M16.76 18.29V13.71H19.8V12.19H12.19V13.71H15.23V18.29H6.09V19.81H15.23V24.38H13.71V25.9H12.19V30.48H13.71V32H18.28V30.48H19.8V25.9H18.28V24.38H16.76V19.81H25.9V18.29H16.76Z" />
            <path d="M22.85 3.05H21.33V10.67H22.85V3.05Z" />
            <path d="M21.33 10.67H19.8V12.19H21.33V10.67Z" />
            <path d="M21.33 1.52H19.8V3.05H21.33V1.52Z" />
            <path d="M19.8 7.62H18.28V9.14H19.8V7.62Z" />
            <path d="M19.8 4.57H18.28V6.09H19.8V4.57Z" />
            <path d="M18.28 9.14H13.71V10.67H18.28V9.14Z" />
            <path d="M19.8 0H12.19V1.52H19.8V0Z" />
            <path d="M13.71 7.62H12.19V9.14H13.71V7.62Z" />
            <path d="M13.71 4.57H12.19V6.09H13.71V4.57Z" />
            <path d="M12.19 10.67H10.66V12.19H12.19V10.67Z" />
            <path d="M12.19 1.52H10.66V3.05H12.19V1.52Z" />
            <path d="M10.66 3.05H9.14V10.67H10.66V3.05Z" />
            <path d="M6.09 19.81H4.57V21.33H6.09V19.81Z" />
            <path d="M3.04 24.38H1.52V25.9H0V30.48H1.52V32H6.09V30.48H7.61V25.9H6.09V24.38H4.57V21.33H3.04V24.38Z" />
        </svg>
    );
}
