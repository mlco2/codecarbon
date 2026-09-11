import { useEffect, useRef, useState } from "react";
import { ClipboardCheck, ClipboardCopy, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { createExperiment } from "@/api/experiments";
import { Experiment, ExperimentInput } from "@/api/schemas";
import { Dialog, DialogContent } from "./ui/dialog";
import { FormField } from "./ui/form-field";
import { IconButton } from "./ui/icon-button";
import ModalHeader from "./ui/modal-header";
import { PrimaryButton } from "./ui/primary-button";

/*
 * Create an experiment, in the same panel as the Create-project dialog: the two
 * are the same object in the design, so they share the shell, the fields and the
 * button rather than each describing them.
 *
 * It has a second state the other does not: once the experiment exists, the
 * dialog stays open to hand over its id, since that is what the tracker needs and
 * the page never shows it again.
 */
export default function CreateExperimentModal({
    projectId,
    isOpen,
    onClose,
    onExperimentCreated,
}: {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onExperimentCreated?: () => void | Promise<void>;
}) {
    const [isCopied, setIsCopied] = useState(false);
    const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [isCreated, setIsCreated] = useState(false);
    const [experimentData, setExperimentData] = useState<ExperimentInput>({
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

    useEffect(() => {
        return () => {
            if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
        };
    }, []);

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
            await onExperimentCreated?.();
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
                copyTimerRef.current = setTimeout(
                    () => setIsCopied(false),
                    2000,
                );
            })
            .catch((err) => {
                console.error("Failed to copy experiment id:", err);
                toast.error("Failed to copy experiment ID");
            });
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent
                hideClose
                className="max-w-[560px] gap-0 rounded-none border-2 border-black bg-cc-background p-0 shadow-dialog"
            >
                {!isCreated ? (
                    <>
                        <ModalHeader title="Create experiment" />

                        <form
                            className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10"
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleSave();
                            }}
                        >
                            <FormField
                                id="experiment-name"
                                label="Name"
                                placeholder="Name"
                                required
                                value={experimentData.name}
                                onChange={(e) =>
                                    setExperimentData({
                                        ...experimentData,
                                        name: e.target.value,
                                    })
                                }
                            />

                            <FormField
                                id="experiment-description"
                                label="Description"
                                placeholder="Description"
                                value={experimentData.description}
                                onChange={(e) =>
                                    setExperimentData({
                                        ...experimentData,
                                        description: e.target.value,
                                    })
                                }
                            />

                            <div className="flex pt-4">
                                <PrimaryButton
                                    type="submit"
                                    disabled={
                                        isSaving || !experimentData.name.trim()
                                    }
                                >
                                    {isSaving && (
                                        <Loader2 className="size-4 animate-spin motion-reduce:animate-none" />
                                    )}
                                    {isSaving
                                        ? "Creating..."
                                        : "Create experiment"}
                                </PrimaryButton>
                            </div>
                        </form>
                    </>
                ) : (
                    <>
                        <ModalHeader
                            title={`${createdExperiment?.name} created`}
                        />

                        <div className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10">
                            <div className="flex flex-col gap-1">
                                <p className="type-mono-regular type-field text-cc-white">
                                    Id of this experiment
                                </p>
                                <div className="flex items-center gap-2">
                                    <code className="type-mono-regular type-field flex h-control min-w-0 flex-1 items-center overflow-x-auto rounded-field bg-white/5 px-4 text-cc-text-input-gray">
                                        {createdExperiment?.id}
                                    </code>
                                    <IconButton
                                        aria-label="Copy experiment ID"
                                        onClick={() =>
                                            handleCopy(createdExperiment?.id)
                                        }
                                    >
                                        {isCopied ? (
                                            <ClipboardCheck className="size-5" />
                                        ) : (
                                            <ClipboardCopy className="size-5" />
                                        )}
                                    </IconButton>
                                </div>
                            </div>

                            <div className="flex pt-4">
                                <PrimaryButton onClick={handleClose}>
                                    Done
                                </PrimaryButton>
                            </div>
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
