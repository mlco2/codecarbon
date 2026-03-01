import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { AlertTriangle, Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface DeleteProjectModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    projectName: string;
    projectId: string;
    onDelete: (projectId: string) => Promise<void>;
}

export default function DeleteProjectModal({
    open,
    onOpenChange,
    projectName,
    projectId,
    onDelete,
}: DeleteProjectModalProps) {
    const [confirmationText, setConfirmationText] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);

    const isConfirmationValid = confirmationText === projectName;

    const handleDelete = async () => {
        if (!isConfirmationValid) return;

        setIsDeleting(true);
        try {
            await onDelete(projectId);
            onOpenChange(false);
            setConfirmationText("");
        } catch (error) {
            console.error("Error deleting project:", error);
        } finally {
            setIsDeleting(false);
        }
    };

    const handleCancel = () => {
        setConfirmationText("");
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-destructive">
                        <AlertTriangle className="h-5 w-5" />
                        Delete Project
                    </DialogTitle>
                    <DialogDescription>
                        This action cannot be undone. This will permanently
                        delete the project and all associated data.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Warning</AlertTitle>
                        <AlertDescription className="mt-2 text-sm">
                            Deleting this project will permanently remove:
                            <ul className="list-disc list-inside mt-2 space-y-1">
                                <li>All experiments in this project</li>
                                <li>All runs and their data</li>
                                <li>All emission records</li>
                                <li>All API tokens for this project</li>
                            </ul>
                        </AlertDescription>
                    </Alert>

                    <div className="space-y-2">
                        <Label htmlFor="confirm-name">
                            To confirm, type{" "}
                            <span className="font-mono font-bold bg-muted px-1 py-0.5 rounded">
                                {projectName}
                            </span>{" "}
                            below:
                        </Label>
                        <Input
                            id="confirm-name"
                            value={confirmationText}
                            onChange={(e) =>
                                setConfirmationText(e.target.value)
                            }
                            placeholder={projectName}
                            className="font-mono"
                            disabled={isDeleting}
                            autoComplete="off"
                        />
                    </div>
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={isDeleting}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleDelete}
                        disabled={!isConfirmationValid || isDeleting}
                    >
                        {isDeleting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Deleting...
                            </>
                        ) : (
                            "Delete Project"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
