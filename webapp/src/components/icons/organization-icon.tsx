/*
 * Organization icon — an office building, used for each organization in the
 * account menu.
 *
 * Supplied directly rather than exported from Figma, which is why it sits
 * outside `figma-icons.tsx` — everything in that file traces to a Figma node.
 * Every drawn element carries `currentColor`, so the menu row's hover and
 * selected colours drive it like the other glyphs.
 *
 * The source also contains a `<path d="M0 0h24v24H0z" fill="none" />`, the usual
 * bounding-box spacer. It draws nothing and the viewBox already covers the same
 * 24x24 area, so it is left out.
 */

type IconProps = {
    className?: string;
};

export function OrganizationIcon({ className }: IconProps) {
    return (
        <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
            className={className}
        >
            <rect
                width="2"
                height="2"
                x="9"
                y="6"
                fill="currentColor"
                rx=".5"
            />
            <rect
                width="2"
                height="2"
                x="13"
                y="6"
                fill="currentColor"
                rx=".5"
            />
            <rect
                width="2"
                height="2"
                x="9"
                y="9.5"
                fill="currentColor"
                rx=".5"
            />
            <rect
                width="2"
                height="2"
                x="13"
                y="9.5"
                fill="currentColor"
                rx=".5"
            />
            <rect
                width="2"
                height="2"
                x="9"
                y="13"
                fill="currentColor"
                rx=".5"
            />
            <rect
                width="2"
                height="2"
                x="13"
                y="13"
                fill="currentColor"
                rx=".5"
            />
            <path
                fill="currentColor"
                d="M18.25 19.25h-.5V4a.76.76 0 0 0-.75-.75H7a.76.76 0 0 0-.75.75v15.25h-.5a.75.75 0 0 0 0 1.5h12.5a.75.75 0 0 0 0-1.5m-2 0H11V17a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v2.25H7.75V4.75h8.5Z"
            />
        </svg>
    );
}
