import { FigmaIconProps } from "./types";

/*
 * Organizations icon — a building with two wings, drawn in the same pixel-art
 * style as the rail's other icons. Distinct from `OrganizationIcon`, the thin
 * glyph the menu rows use.
 *
 * The artwork only fills the middle of its original canvas, so the viewBox is
 * cropped to a square around it to fill the 32px frame like its siblings.
 */

export function OrganizationsIcon({ className }: FigmaIconProps) {
    return (
        <svg
            viewBox="275 288 704 704"
            width="32"
            height="32"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            {/* Center tower */}
            <rect x="504" y="393" width="246" height="33" />
            <rect x="471" y="426" width="33" height="428" />
            <rect x="750" y="426" width="33" height="428" />
            {/* Center windows */}
            <rect x="553" y="475" width="56" height="56" />
            <rect x="645" y="475" width="56" height="56" />
            <rect x="553" y="568" width="56" height="56" />
            <rect x="645" y="568" width="56" height="56" />
            <rect x="553" y="661" width="56" height="56" />
            <rect x="645" y="661" width="56" height="56" />
            {/* Door */}
            <rect x="553" y="752" width="148" height="28" />
            <rect x="553" y="780" width="33" height="74" />
            <rect x="668" y="780" width="33" height="74" />
            {/* Left wing */}
            <rect x="308" y="549" width="163" height="33" />
            <rect x="275" y="582" width="33" height="272" />
            <rect x="345" y="629" width="56" height="56" />
            <rect x="345" y="724" width="56" height="56" />
            {/* Right wing */}
            <rect x="783" y="549" width="163" height="33" />
            <rect x="946" y="582" width="33" height="272" />
            <rect x="853" y="629" width="56" height="56" />
            <rect x="853" y="724" width="56" height="56" />
            {/* Base */}
            <rect x="275" y="854" width="704" height="33" />
        </svg>
    );
}
