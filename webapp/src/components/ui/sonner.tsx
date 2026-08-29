import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

/*
 * The app's notifications.
 *
 * `unstyled` is load-bearing: Sonner's visual rules hang off
 * `[data-sonner-toast][data-styled='true']`, in a stylesheet it injects after
 * Tailwind's, so a class can neither outrank them nor win on order. Unstyled
 * drops that layer while keeping Sonner's positioning and animation, which is
 * why the flex row, the gap and the icon's box are restated below.
 *
 * The design draws only the success alert; the other variants keep the dark
 * surface and take just its shape.
 */

const Toaster = ({ ...props }: ToasterProps) => {
    return (
        <Sonner
            theme="dark"
            position="top-right"
            className="toaster group"
            toastOptions={{
                unstyled: true,
                classNames: {
                    /* Shape, layout and the surface every variant keeps
                       unless it overrides one. `w-fit` rather than `w-auto`:
                       the toast is a block in a fixed 356px column, where auto
                       means "fill it" — the design sizes it to its message —
                       and `ml-auto` keeps it against the column's right edge.
                    */
                    toast:
                        "ml-auto flex w-fit items-center gap-2.5 rounded-menu border px-9 py-3.5 " +
                        "font-mono text-[14px] shadow-menu border-border bg-background text-foreground",
                    /* Sonner puts a variant's classes on the same element as
                       the base ones above — and puts `default` there too, on
                       every toast — so an override competing at equal weight
                       would be settled by stylesheet order rather than by
                       intent. These are marked important to settle it here. */
                    success:
                        "!border-cc-lime !bg-cc-button-hover !text-cc-background",
                    /* Sonner sizes the icon box itself only when styled. */
                    icon: "flex size-5 shrink-0 items-center justify-center",
                    title: "font-mono font-bold",
                    description: "font-mono opacity-80",
                    actionButton:
                        "rounded-field bg-cc-background px-3 py-1 font-mono text-cc-white",
                    cancelButton:
                        "rounded-field bg-muted px-3 py-1 font-mono text-muted-foreground",
                },
            }}
            {...props}
        />
    );
};

export { Toaster };
