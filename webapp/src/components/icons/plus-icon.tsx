/*
 * Plus icon, used by the account menu's "Add new organization" row.
 *
 * Supplied directly rather than exported from Figma, which is why it sits
 * outside `figma-icons.tsx` — everything in that file traces to a Figma node.
 * It draws with `currentColor` so the row's hover colour reaches it.
 *
 * The source also contains a `<path d="M0 0h24v24H0z" fill="none" />`, the usual
 * bounding-box spacer. It draws nothing and the viewBox already covers the same
 * 24x24 area, so it is left out.
 */

type IconProps = {
    className?: string;
};

export function PlusIcon({ className }: IconProps) {
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
            <path
                fill="currentColor"
                d="M19 12.998h-6v6h-2v-6H5v-2h6v-6h2v6h6z"
            />
        </svg>
    );
}
