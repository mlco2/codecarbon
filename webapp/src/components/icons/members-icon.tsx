/*
 * Members icon — two figures side by side, drawn in the same pixel-art style as
 * the rail's other icons.
 *
 * Unlike the icons in `figma-icons.tsx`, this one was supplied directly rather
 * than exported from the Figma file, which is why it lives in its own module:
 * that file's contents are all traceable to a Figma node, and this is not.
 *
 * `shape-rendering="crispEdges"` keeps the pixel grid sharp by disabling
 * anti-aliasing, which matters for artwork built from whole-pixel rectangles.
 * The glyph takes its colour from `currentColor`, so the rail's selected and
 * hover states drive it exactly as they do the others.
 */

type IconProps = {
    className?: string;
};

export function MembersIcon({ className }: IconProps) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 32 32"
            fill="none"
            shapeRendering="crispEdges"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            <g fill="currentColor">
                <path d="M14 2H18V4H14Z" />
                <path d="M13 3H14V5H13Z" />
                <path d="M18 3H19V5H18Z" />
                <path d="M12 4H13V10H12Z" />
                <path d="M19 4H20V10H19Z" />
                <path d="M11 5H12V9H11Z" />
                <path d="M20 5H21V9H20Z" />
                <path d="M4 8H7V10H4Z" />
                <path d="M25 8H28V10H25Z" />
                <path d="M3 9H4V11H3Z" />
                <path d="M7 9H8V11H7Z" />
                <path d="M13 9H14V11H13Z" />
                <path d="M18 9H19V11H18Z" />
                <path d="M24 9H25V11H24Z" />
                <path d="M28 9H29V11H28Z" />
                <path d="M2 10H3V15H2Z" />
                <path d="M8 10H9V15H8Z" />
                <path d="M14 10H18V12H14Z" />
                <path d="M23 10H24V15H23Z" />
                <path d="M29 10H30V15H29Z" />
                <path d="M1 11H2V14H1Z" />
                <path d="M9 11H10V14H9Z" />
                <path d="M22 11H23V14H22Z" />
                <path d="M30 11H31V14H30Z" />
                <path d="M12 13H20V15H12Z" />
                <path d="M3 14H4V16H3Z" />
                <path d="M7 14H8V16H7Z" />
                <path d="M11 14H12V16H11Z" />
                <path d="M20 14H21V16H20Z" />
                <path d="M24 14H25V16H24Z" />
                <path d="M28 14H29V16H28Z" />
                <path d="M4 15H7V17H4Z" />
                <path d="M9 15H11V17H9Z" />
                <path d="M21 15H23V17H21Z" />
                <path d="M25 15H28V17H25Z" />
                <path d="M8 16H9V30H8Z" />
                <path d="M23 16H24V30H23Z" />
                <path d="M7 17H8V30H7Z" />
                <path d="M24 17H25V30H24Z" />
                <path d="M3 18H6V20H3Z" />
                <path d="M26 18H29V20H26Z" />
                <path d="M2 19H3V30H2Z" />
                <path d="M29 19H30V30H29Z" />
                <path d="M1 20H2V30H1Z" />
                <path d="M30 20H31V30H30Z" />
                <path d="M3 28H6V30H3Z" />
                <path d="M9 28H23V30H9Z" />
                <path d="M26 28H29V30H26Z" />
            </g>
        </svg>
    );
}
