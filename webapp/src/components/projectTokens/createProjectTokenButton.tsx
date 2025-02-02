"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import ProjectTokenModal from "@/components/projectTokens/modal";

const CreateTokenButton = ({
    projectId,
    onTokenCreated,
}: {
    projectId: string;
    onTokenCreated: () => void;
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
            <ProjectTokenModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onTokenCreated={onTokenCreated}
                projectId={projectId}
            />
        </div>
    );
};

export default CreateTokenButton;
