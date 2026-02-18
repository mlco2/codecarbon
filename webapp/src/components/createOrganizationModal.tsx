"use client";

import { useState } from "react";
import { createOrganization } from "@/server-functions/organizations";
import { Separator } from "./ui/separator";
import { Input } from "./ui/input";
import { Organization } from "@/types/organization";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "./ui/dialog";

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
    const router = useRouter();

    const handleSave = async () => {
        if (!formData.name.trim()) {
            toast.error("Organization name is required");
            return;
        }

        setIsLoading(true);

        toast
            .promise(
                (async () => {
                    const newOrganization = await createOrganization(formData);
                    await onOrganizationCreated();
                    setFormData({ name: "", description: "" });
                    onClose();
                    if (newOrganization) {
                        router.push(`/${newOrganization.id}`);
                        return newOrganization;
                    } else {
                        throw new Error("Failed to create organization");
                    }
                })(),
                {
                    loading: "Creating organization...",
                    success: "Organization created",
                    error: "Failed to create organization",
                },
            )
            .unwrap();
        setIsLoading(false);
    };

    const handleClose = () => {
        setFormData({ name: "", description: "" });
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Create new organization</DialogTitle>
                    <DialogDescription>
                        Fill in the details to create your organization
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
                        placeholder="Organization Name"
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
                        placeholder="Organization Description"
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

export default CreateOrganizationModal;
