import { useState } from "react";
import { Project } from "@/types/project";
import { createProject } from "@/server-functions/projects";
import { Separator } from "./ui/separator";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "./ui/dialog";
import { toast } from "sonner";

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

    const handleClose = () => {
        // Reset state when closing
        setFormData({ name: "", description: "" });
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Create new project</DialogTitle>
                    <DialogDescription>
                        Fill in the details to create your project
                    </DialogDescription>
                </DialogHeader>
                <Separator className="my-4" />
                <div className="grid gap-4 py-4">
                    <Input
                        type="text"
                        value={formData.name}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                name: e.target.value,
                            })
                        }
                        placeholder="Project Name"
                    />
                    <Input
                        type="text"
                        value={formData.description}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                description: e.target.value,
                            })
                        }
                        placeholder="Project Description"
                    />
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={handleClose}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={isLoading}>
                        {isLoading ? "Creating..." : "Create"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default CreateProjectModal;
