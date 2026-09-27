import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { AlertTriangle, Loader2 } from "lucide-react";

interface RemoveMemberModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    memberName: string;
    memberId: string;
    organizationName: string;
    onRemove: (memberId: string) => Promise<void>;
}

export default function RemoveMemberModal({
    open,
    onOpenChange,
    memberName,
    memberId,
    organizationName,
    onRemove,
}: RemoveMemberModalProps) {
    const [isRemoving, setIsRemoving] = useState(false);

    const handleRemove = async () => {
        setIsRemoving(true);
        try {
            await onRemove(memberId);
            onOpenChange(false);
        } catch (error) {
            console.error("Error removing member:", error);
        } finally {
            setIsRemoving(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-destructive">
                        <AlertTriangle className="h-5 w-5" />
                        Remove member
                    </DialogTitle>
                    <DialogDescription>
                        <span className="font-medium">{memberName}</span> will
                        lose access to {organizationName} and all of its
                        projects. Their emission data is kept, and they can be
                        added back later.
                    </DialogDescription>
                </DialogHeader>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={isRemoving}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleRemove}
                        disabled={isRemoving}
                    >
                        {isRemoving ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Removing...
                            </>
                        ) : (
                            "Remove member"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
