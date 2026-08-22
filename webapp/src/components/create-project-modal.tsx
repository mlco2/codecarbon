import { useState } from "react";
import { toast } from "sonner";

import { createProject } from "@/api/projects";
import { Dialog, DialogContent } from "./ui/dialog";
import ModalHeader from "./ui/modal-header";
import { FormField } from "./ui/form-field";
import { PrimaryButton } from "./ui/primary-button";

/*
 * Create a project.
 *
 * Proportions are taken from the design rather than copied off it. Its fixed
 * 664x524 panel cannot be reproduced as a size — its own numbers do not add up,
 * with the form starting below where the panel ends — but its proportion, a little
 * wider than tall, is what makes it read as a dialog rather than as a bar. So the
 * panel is built to land near it:
 *
 *   - the maximum width is 560, not 664. Reproducing 664 against a height that
 *     follows the content gave a distinctly wider box; pulling the width in
 *     recovers the near-square proportion, and it costs nothing because the form
 *     is two single-line fields
 *   - the title stays at display size while the box around it narrows, at 24px
 *     rather than the design's 32
 *   - the vertical padding is generous, but bounded by how it looks rather than by
 *     the ratio it produces. Pushed far enough to force the design's exact
 *     proportion it just looks empty, so the panel sits a little wider than tall
 *
 * The design's two horizontal measurements disagree — the title row is inset 33px
 * from the panel edge while the form is a 466px column centred in the 664px panel,
 * 99px either side. They are normalised to a single gutter here, as the redesigned
 * pages do, so the title and the fields share one left edge instead of stepping in
 * twice.
 *
 * Below its maximum the panel narrows, and `DialogContent` scrolls it if it ever
 * exceeds the viewport, so the modal is usable on a phone.
 *
 * The design's ✕ is its "add" glyph rotated 45 degrees — that is how the file
 * builds it — so it renders as the same `PlusIcon` under a `rotate-45`, rather
 * than as a second asset that would have to stay in step with the first.
 *
 * Two things in the design were confirmed as component defaults rather than
 * intent: the envelope icon inside the Name field (its Input component was built
 * for an email address, and the Description field below it has no icon), which is
 * dropped; and the absence of a Cancel button, which is kept — the ✕, the Esc key
 * and a click outside all still close the dialog.
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
