"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import Modal from "@/components/projectTokens/modal";
import { createProjectToken } from "@/server-functions/projectTokens";

const CreateTokenButton = ({
    projectId,
    onTokenCreated,
}: {
    projectId: string;
    onTokenCreated: () => Promise<void>;
}) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const handleClick = async () => {
        setIsModalOpen(true);
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
                onClose={() => setIsModalOpen(false)}
                onTokenCreated={onTokenCreated}
                projectId={projectId}
            />
        </div>
    );
};

export default CreateTokenButton;
