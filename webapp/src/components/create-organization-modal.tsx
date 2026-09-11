import { useState } from "react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

import { createOrganization } from "@/api/organizations";
import { Dialog, DialogContent } from "./ui/dialog";
import { FormField } from "./ui/form-field";
import ModalHeader from "./ui/modal-header";
import { PrimaryButton } from "./ui/primary-button";

/*
 * Create an organization, in the same panel as the Create-project dialog: the
 * two are the same object in the design, so they share the shell, the fields
 * and the button rather than each describing them.
 */

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    onOrganizationCreated: () => Promise<void>;
}

interface CreateOrganizationInput {
    name: string;
    description: string;
}

const CreateOrganizationModal: React.FC<ModalProps> = ({
    isOpen,
    onClose,
    onOrganizationCreated,
}) => {
    const [formData, setFormData] = useState<CreateOrganizationInput>({
        name: "",
        description: "",
    });
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

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
                    const newOrganization = await createOrganization(formData);
                    if (!newOrganization) {
                        throw new Error("Failed to create organization");
                    }
                    await onOrganizationCreated();
                    handleClose();
                    navigate(`/${newOrganization.id}`);
                    return newOrganization;
                } catch (error) {
                    console.error("Failed to create organization:", error);
                    throw error;
                } finally {
                    setIsLoading(false);
                }
            },
            {
                loading: "Creating organization...",
                success: "Organization created successfully!",
                error: "Failed to create organization",
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
                <ModalHeader title="Create organization" />

                <form
                    className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10"
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <FormField
                        id="organization-name"
                        label="Name"
                        placeholder="Name"
                        required
                        value={formData.name}
                        onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                        }
                    />

                    <FormField
                        id="organization-description"
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

                    <div className="flex pt-4">
                        <PrimaryButton
                            type="submit"
                            disabled={isLoading || !formData.name.trim()}
                        >
                            {isLoading ? "Creating..." : "Create organization"}
                        </PrimaryButton>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default CreateOrganizationModal;
