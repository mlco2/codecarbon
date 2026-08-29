import { useState } from "react";
import { toast } from "sonner";

import { createProject } from "@/api/projects";
import { Dialog, DialogContent } from "./ui/dialog";
import ModalHeader from "./ui/modal-header";
import { FormField } from "./ui/form-field";
import { PrimaryButton } from "./ui/primary-button";

/*
 * Create a project: a dialog holding a name and a description.
 *
 * The design's fixed 664x524 panel is not reproduced as a size — its own
 * numbers do not add up, with the form starting below where the panel ends — so
 * the panel keeps its proportion instead, a little wider than tall, and narrows
 * below its maximum.
 */

interface ModalProps {
    organizationId: string;
    isOpen: boolean;
    onClose: () => void;
    onProjectCreated: () => Promise<void>;
}

interface CreateProjectInput {
    name: string;
    description: string;
}

const CreateProjectModal: React.FC<ModalProps> = ({
    organizationId,
    isOpen,
    onClose,
    onProjectCreated,
}) => {
    const [formData, setFormData] = useState<CreateProjectInput>({
        name: "",
        description: "",
    });
    const [isLoading, setIsLoading] = useState(false);

    const handleClose = () => {
        // Reset state when closing
        setFormData({ name: "", description: "" });
        onClose();
    };

    const handleSave = async () => {
        toast.promise(
            async () => {
                setIsLoading(true);
                try {
                    const newProject = await createProject(
                        organizationId,
                        formData,
                    );
                    await onProjectCreated(); // Call the callback to refresh the project list
                    handleClose(); // Automatically close the modal after successful creation
                    return newProject; // Return for the success message
                } catch (error) {
                    console.error("Failed to create project:", error);
                    throw error; // Rethrow for the error message
                } finally {
                    setIsLoading(false);
                }
            },
            {
                loading: "Creating project...",
                success: "Project created successfully!",
                error: "Failed to create project",
            },
        );
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            {/* The design's own close control lives in the header, so the shared
                corner button is omitted. */}
            <DialogContent
                hideClose
                className="max-w-[560px] gap-0 rounded-none border-2 border-black bg-cc-background p-0 shadow-dialog"
            >
                <ModalHeader title="Create project" />

                {/* The form shares the header's gutter. Its vertical padding is
                    the panel's main source of air. */}
                <form
                    className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10"
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <FormField
                        id="project-name"
                        label="Name"
                        placeholder="Name"
                        required
                        value={formData.name}
                        onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                        }
                    />

                    <FormField
                        id="project-description"
                        label="Description"
                        placeholder="Description"
                        value={formData.description}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                description: e.target.value,
                            })
                        }
                    />

                    {/* Separated by more than the gap between the fields, so it
                        reads as the end of the form rather than a third row. */}
                    <div className="flex pt-4">
                        <PrimaryButton
                            type="submit"
                            disabled={isLoading || !formData.name.trim()}
                        >
                            {isLoading ? "Creating..." : "Create project"}
                        </PrimaryButton>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default CreateProjectModal;
