import { PlusIcon } from "@/components/icons/plus-icon";
import { DialogClose, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/helpers/utils";

/*
 * A dialog's header, as the design draws it: the title in the display face with
 * the close control beside it, above the rule that separates it from the body.
 *
 * The ✕ is the design's "add" glyph rotated 45 degrees — that is how the file
 * builds it — so it renders as the same `PlusIcon` under a `rotate-45`, rather
 * than a second asset that would have to stay in step with the first. Dialogs
 * using this header pass `hideClose` to `DialogContent`, since this is their close
 * control.
 *
 * The title's size is set here with utilities rather than through a `type-*`
 * class, deliberately: `DialogTitle` ships a `text-lg` of its own, and because
 * `twMerge` cannot tell that a project class is a font-size it leaves both in
 * place — then `text-lg` wins, being a utility, and the title renders at 18px.
 * Naming the size as a utility is what lets the merge drop the one it replaces.
 */
export default function ModalHeader({
    title,
    className,
    children,
}: Readonly<{
    title: string;
    className?: string;
    /** Optional controls placed before the close button. */
    children?: React.ReactNode;
}>) {
    return (
        <DialogHeader
            className={cn(
                "space-y-0 border-b border-cc-rule px-6 pb-6 pt-6 text-left sm:px-10",
                className,
            )}
        >
            <div className="flex items-center justify-between gap-4">
                <DialogTitle className="type-display min-w-0 text-xl font-normal leading-normal tracking-normal text-cc-white md:text-2xl">
                    {title}
                </DialogTitle>

                <div className="flex shrink-0 items-center gap-2">
                    {children}

                    <DialogClose className="-mr-2 flex size-12 shrink-0 cursor-pointer items-center justify-center rounded-field text-cc-white outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime motion-reduce:transition-none">
                        <PlusIcon className="size-8 rotate-45" />
                        <span className="sr-only">Close</span>
                    </DialogClose>
                </div>
            </div>
        </DialogHeader>
    );
}
