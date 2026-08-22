/*
 * Account icon — a head and shoulders in a circle, drawn in the same pixel-art
 * style as the rail's other icons.
 *
 * Supplied directly rather than exported from Figma, which is why it sits
 * outside `figma-icons.tsx` — everything in that file traces to a Figma node.
 * The glyph takes its colour from `currentColor`, so the rail's hover and
 * pressed states drive it exactly as they do the other items.
 */

type IconProps = {
    className?: string;
};

export function AccountIcon({ className }: IconProps) {
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
            <path d="M10.67 0H21.33V1.52H10.67Z" />
            <path d="M7.62 1.52H10.67V3.05H7.62Z" />
            <path d="M21.33 1.52H24.38V3.05H21.33Z" />
            <path d="M6.1 3.05H7.62V4.57H6.1Z" />
            <path d="M24.38 3.05H25.9V4.57H24.38Z" />
            <path d="M4.57 4.57H6.1V6.1H4.57Z" />
            <path d="M13.71 4.57H18.29V6.1H13.71Z" />
            <path d="M25.9 4.57H27.43V6.1H25.9Z" />
            <path d="M3.05 6.1H4.57V7.62H3.05Z" />
            <path d="M12.19 6.1H13.71V7.62H12.19Z" />
            <path d="M18.29 6.1H19.81V7.62H18.29Z" />
            <path d="M27.43 6.1H28.95V7.62H27.43Z" />
            <path d="M1.52 7.62H3.05V10.67H1.52Z" />
            <path d="M10.67 7.62H12.19V12.19H10.67Z" />
            <path d="M19.81 7.62H21.33V12.19H19.81Z" />
            <path d="M28.95 7.62H30.48V10.67H28.95Z" />
            <path d="M0 10.67H1.52V21.33H0Z" />
            <path d="M30.48 10.67H32V21.33H30.48Z" />
            <path d="M12.19 12.19H13.71V13.71H12.19Z" />
            <path d="M18.29 12.19H19.81V13.71H18.29Z" />
            <path d="M13.71 13.71H18.29V15.24H13.71Z" />
            <path d="M12.19 16.76H19.81V18.29H12.19Z" />
            <path d="M10.67 18.29H12.19V19.81H10.67Z" />
            <path d="M19.81 18.29H21.33V19.81H19.81Z" />
            <path d="M9.14 19.81H10.67V21.33H9.14Z" />
            <path d="M21.33 19.81H22.86V21.33H21.33Z" />
            <path d="M1.52 21.33H3.05V24.38H1.52Z" />
            <path d="M7.62 21.33H9.14V25.9H7.62Z" />
            <path d="M22.86 21.33H24.38V25.9H22.86Z" />
            <path d="M28.95 21.33H30.48V24.38H28.95Z" />
            <path d="M3.05 24.38H4.57V25.9H3.05Z" />
            <path d="M9.14 24.38H22.86V25.9H9.14Z" />
            <path d="M27.43 24.38H28.95V25.9H27.43Z" />
            <path d="M4.57 25.9H6.1V27.43H4.57Z" />
            <path d="M25.9 25.9H27.43V27.43H25.9Z" />
            <path d="M6.1 27.43H7.62V28.95H6.1Z" />
            <path d="M24.38 27.43H25.9V28.95H24.38Z" />
            <path d="M7.62 28.95H10.67V30.48H7.62Z" />
            <path d="M21.33 28.95H24.38V30.48H21.33Z" />
            <path d="M10.67 30.48H21.33V32H10.67Z" />
        </svg>
    );
}
