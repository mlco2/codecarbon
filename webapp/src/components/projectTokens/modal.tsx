import { IProjectToken } from "@/types/project";
import React, { useState } from "react";
import { ClipboardCopy } from "lucide-react";
import { createProjectToken } from "@/server-functions/projectTokens";
import GeneralModal from "../ui/modal";

interface ModalProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onTokenCreated: () => Promise<void>;
}

const ProjectTokenModal: React.FC<ModalProps> = ({
    projectId,
    isOpen,
    onClose,
    onTokenCreated,
}) => {
    const initialData = { name: "" };
    const handleSave = async (data: { name: string }) => {
        const access = 2;
        const newToken = await createProjectToken(projectId, data.name, access);
        await onTokenCreated(); // Call the callback to refresh the token list
        return newToken;
    };

    const handleCopy = (token: string) => {
        navigator.clipboard
            .writeText(token)
            .then(() => {
                alert("Token copied to clipboard");
            })
            .catch((err) => {
                console.error("Failed to copy token: ", err);
            });
    };

    const renderForm = (data: any, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new token</h2>
            <input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                className="border p-2 w-full"
                placeholder="Token Name"
            />
        </div>
    );
    const renderSavedData = (data: any, setSavedData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Token Created</h2>
            <p className="text-l mb-4">
                The following token has been generated:
            </p>
            <div className="bg-muted flex items-center p-2 rounded ">
                <pre className="m-0">
                    <code>{data.token}</code>
                </pre>
                <button
                    onClick={() => handleCopy(data.token)}
                    className="ml-2 px-4 py-2 rounded text-gray-500 hover:text-gray-700"
                >
                    <ClipboardCopy />
                </button>
            </div>
        </div>
    );
    return (
        <GeneralModal
            isOpen={isOpen}
            onClose={onClose}
            onSave={handleSave}
            initialData={initialData}
            initialSavedData={initialData}
            renderForm={renderForm}
            renderSavedData={renderSavedData}
        />
    );
};

export default ProjectTokenModal;
