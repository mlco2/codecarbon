"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import Modal from "@/components/projectTokens/modal";
import { createProjectToken } from "@/server-functions/projectTokens";

interface CreateTokenButtonProps {
    projectId: string;
    onTokenCreated: () => void;
}
const CreateTokenButton: React.FC<CreateTokenButtonProps> = (
    { projectId },
    onTokenCreated,
) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const handleClick = async () => {
        setIsModalOpen(true);
    };
    const onSave = async (tokenName: string) => {
        const access = 2;
        const newToken = await createProjectToken(projectId, tokenName, access);
        console.log("ProjectSettingsPage: createProjectToken", newToken);
        await onTokenCreated(); // Call the callback to refresh the token list
        return newToken;
    };

    return (
        <div>
            <Button
                className="bg-primary text-primary-foreground"
                onClick={handleClick}
            >
                + Create a new token
            </Button>
            <Modal
                isOpen={isModalOpen}
                onSave={onSave}
                onClose={() => setIsModalOpen(false)}
            />
        </div>
    );
};

export default CreateTokenButton;
