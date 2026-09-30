import { Dialog, DialogContent, DialogDescription } from "./ui/dialog";
import ModalHeader from "./ui/modal-header";
import { PrimaryButton } from "./ui/primary-button";
import { SecondaryButton } from "./ui/secondary-button";

/*
 * Confirm removing a member from the organization.
 *
 * The same shell as the create dialogs, with the form replaced by a sentence and
 * a pair of buttons: removal takes no input, and the API refuses to remove an
 * administrator, so the only thing left to establish is that the right person
 * was picked. There is no type-the-name gate as on project deletion — this
 * destroys nothing, and the page's own invite field puts the member back.
 */
export default function RemoveMemberModal({
    isOpen,
    onClose,
    onConfirm,
    memberName,
    isRemoving,
}: Readonly<{
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    /** Their name, or their email address when the API has no name. */
    memberName: string;
    isRemoving: boolean;
}>) {
    return (
        <Dialog
            open={isOpen}
            onOpenChange={(open) => {
                if (!open && !isRemoving) onClose();
            }}
        >
            {/* The design's own close control lives in the header, so the shared
                corner button is omitted. */}
            <DialogContent
                hideClose
                className="max-w-[560px] gap-0 rounded-none border-2 border-black bg-cc-background p-0 shadow-dialog"
            >
                <ModalHeader title="Remove member" />

                <div className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10">
                    <DialogDescription className="type-mono-regular type-field break-words text-cc-white">
                        Remove {memberName} from this organization? They lose
                        access to its projects, and can be invited back by
                        email.
                    </DialogDescription>

                    <div className="flex flex-wrap gap-4 pt-4">
                        <PrimaryButton
                            type="button"
                            onClick={onConfirm}
                            disabled={isRemoving}
                        >
                            {isRemoving ? "Removing..." : "Remove member"}
                        </PrimaryButton>
                        <SecondaryButton
                            onClick={onClose}
                            disabled={isRemoving}
                        >
                            Cancel
                        </SecondaryButton>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
