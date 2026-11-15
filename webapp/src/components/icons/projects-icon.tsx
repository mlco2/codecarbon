import { FigmaIconProps } from "./types";

/*
 * Projects icon — two magazine files with documents standing in them, a smiley face
 * on the front one, drawn in the same pixel-art style as the rail's other icons.
 */

export function ProjectsIcon({ className }: FigmaIconProps) {
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
            <path d="M28.96 6.1V0H13.72V1.52H7.62V3.05H3.05V13.72H1.53V16.76H0V32H32V6.1H28.96ZM7.62 30.48H1.53V21.33H7.62V30.48ZM7.62 19.81H4.58V4.57H7.62V19.81ZM9.15 3.05H13.72V4.57H10.67V19.81H9.15V3.05ZM13.72 6.1V19.81H12.2V6.1H13.72ZM15.24 30.48H9.15V21.33H15.24V30.48ZM30.48 30.48H16.77V19.81H15.24V1.52H27.43V6.1H22.86V7.62H30.48V30.48Z" />
            <path d="M27.43 21.33H25.91V22.86H27.43V21.33Z" />
            <path d="M27.43 18.29H25.91V19.81H27.43V18.29Z" />
            <path d="M25.91 22.86H22.86V24.38H25.91V22.86Z" />
            <path d="M22.86 21.33H21.34V22.86H22.86V21.33Z" />
            <path d="M22.86 18.29H21.34V19.81H22.86V18.29Z" />
            <path d="M22.86 7.62H21.34V10.67H22.86V7.62Z" />
            <path d="M21.34 10.67H19.81V13.72H21.34V10.67Z" />
            <path d="M19.81 13.72H18.29V16.76H19.81V13.72Z" />
            <path d="M19.81 3.05H18.29V4.57H19.81V3.05Z" />
            <path d="M18.29 16.76H16.77V19.81H18.29V16.76Z" />
            <path d="M13.72 24.38H10.67V27.43H13.72V24.38Z" />
            <path d="M6.1 24.38H3.05V27.43H6.1V24.38Z" />
        </svg>
    );
}
