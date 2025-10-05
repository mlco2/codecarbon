"use client";

import { useEffect, useState } from "react";
import { createExperiment } from "@/server-functions/experiments";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Experiment } from "@/types/experiment";
import { Separator } from "./ui/separator";
import { ClipboardCheck, ClipboardCopy, Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";

export default function CreateExperimentModal({
    projectId,
    isOpen,
    onClose,
    onExperimentCreated,
}: {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onExperimentCreated: () => void;
}) {
    const [isCopied, setIsCopied] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isCreated, setIsCreated] = useState(false);
    const [experimentData, setExperimentData] = useState<Experiment>({
        name: "",
        description: "",
        on_cloud: false,
        project_id: "",
    });
    const [createdExperiment, setCreatedExperiment] =
        useState<Experiment | null>(null);

    useEffect(() => {
        if (projectId && !experimentData.project_id) {
            setExperimentData({
                ...experimentData,
                project_id: projectId,
            });
        }
    }, [projectId, experimentData]);

    const resetForm = () => {
        setExperimentData({
            name: "",
            description: "",
            on_cloud: false,
            project_id: projectId,
        });
        setIsCreated(false);
        setCreatedExperiment(null);
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    const handleSave = async () => {
        if (!experimentData.name.trim()) {
            toast.error("Experiment name is required");
            return;
        }

        setIsSaving(true);

        try {
            const newExperiment = await createExperiment(experimentData);
            setCreatedExperiment(newExperiment);
            setIsCreated(true);
            await onExperimentCreated();
            toast.success(
                `Experiment ${experimentData.name} created successfully`,
            );
        } catch (error) {
            console.error("Failed to create experiment:", error);
            toast.error("Failed to create experiment");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCopy = (token: string | undefined) => {
        if (!token) return;
        navigator.clipboard
            .writeText(token)
            .then(() => {
                setIsCopied(true);
                toast.success("Experiment ID copied to clipboard");
                setTimeout(() => setIsCopied(false), 2000);
            })
            .catch((err) => {
                console.error("Failed to copy experiment id:", err);
                toast.error("Failed to copy experiment ID");
            });
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[500px]">
                {!isCreated ? (
                    <>
                        <DialogHeader>
                            <DialogTitle>Create new experiment</DialogTitle>
                        </DialogHeader>
                        <Separator className="my-4" />
                        <div className="space-y-4 py-2">
                            <div className="space-y-2">
                                <Input
                                    type="text"
                                    value={experimentData.name}
                                    onChange={(e) =>
                                        setExperimentData({
                                            ...experimentData,
                                            name: e.target.value,
                                        })
                                    }
                                    placeholder="Experiment Name"
                                />
                            </div>
                            <div className="space-y-2">
                                <Input
                                    type="text"
                                    value={experimentData.description}
                                    onChange={(e) =>
                                        setExperimentData({
                                            ...experimentData,
                                            description: e.target.value,
                                        })
                                    }
                                    placeholder="Experiment Description"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleSave} disabled={isSaving}>
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Create"
                                )}
                            </Button>
                        </DialogFooter>
                    </>
                ) : (
                    <>
                        <DialogHeader>
                            <DialogTitle>
                                Experiment {createdExperiment?.name} Created
                            </DialogTitle>
                        </DialogHeader>
                        <Separator className="my-4" />
                        <div className="py-4">
                            <p className="mb-4">Id of this experiment:</p>
                            <div className="bg-muted flex items-center p-2 rounded justify-between">
                                <pre className="m-1">
                                    <code>{createdExperiment?.id}</code>
                                </pre>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() =>
                                        handleCopy(createdExperiment?.id)
                                    }
                                    className="ml-2"
                                >
                                    {isCopied ? (
                                        <div className="flex items-center gap-2">
                                            <ClipboardCheck className="h-4 w-4" />
                                            <span>Copied</span>
                                        </div>
                                    ) : (
                                        <ClipboardCopy className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleClose}>Done</Button>
                        </DialogFooter>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
