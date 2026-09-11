import { cn } from "@/helpers/utils";

/*
 * A row in the Settings page's sub-navigation.
 *
 * The design draws unselected rows at 50% opacity and gives no hover or pressed
 * state, so those are built from what it does define: hover brings the row to
 * full opacity over a #2b2b2b wash — the same fill the selected row uses — and
 * pressing settles on that fill outright. Disabled rows stay flat.
 *
 * The selected row is not a button. It is the panel you are already on, so there
 * is nothing to press: it renders as a `span` marked `aria-current`, which is
 * also what keeps it out of the tab order.
 */

const ROW =
    "flex items-center gap-0 rounded-menu px-5 py-2.5 text-left outline-none " +
    "focus-visible:ring-2 focus-visible:ring-cc-lime";

const LABEL = "type-display type-settings-nav whitespace-nowrap p-2.5";

export default function SettingsNavItem({
    icon: Icon,
    label,
    isCurrent,
    onClick,
    disabled,
}: Readonly<{
    icon: (props: { className?: string }) => React.JSX.Element;
    label: string;
    isCurrent?: boolean;
    onClick?: () => void;
    disabled?: boolean;
}>) {
    const tone = isCurrent ? "text-cc-lime" : "text-cc-white";

    if (isCurrent) {
        return (
            <span aria-current="page" className={cn(ROW, "bg-cc-darkest-gray")}>
                <Icon className={cn("size-6 shrink-0", tone)} />
                <span className={cn(LABEL, tone)}>{label}</span>
            </span>
        );
    }

    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className={cn(
                ROW,
                "cursor-pointer opacity-50 transition",
                "hover:bg-cc-darkest-gray/50 hover:opacity-100",
                "active:bg-cc-darkest-gray active:opacity-100",
                "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent",
                "motion-reduce:transition-none",
            )}
        >
            <Icon className={cn("size-6 shrink-0", tone)} />
            <span className={cn(LABEL, tone)}>{label}</span>
        </button>
    );
}
