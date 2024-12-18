import { IProjectToken } from "@/types/project";
import React, { useState } from "react";
import { ClipboardCopy, ClipboardCheck } from "lucide-react";
import { createProjectToken } from "@/server-functions/projectTokens";
import GeneralModal from "../ui/modal";
import { Input } from "../ui/input";

interface ModalProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onTokenCreated: () => Promise<void>;
}
interface CreateProjectTokenInput {
    name: string;
}
const ProjectTokenModal: React.FC<ModalProps> = ({
    projectId,
    isOpen,
    onClose,
    onTokenCreated,
}) => {
    const [isCopied, setIsCopied] = useState(false);
    const initialData: CreateProjectTokenInput = { name: "" };
    const initialSavedData: IProjectToken = {
        name: "",
        id: "",
        project_id: "",
        last_used: null,
        token: "",
        access: 0,
    };
    const handleSave = async (
        data: CreateProjectTokenInput,
    ): Promise<IProjectToken> => {
        const access = 2;
        const newToken = await createProjectToken(projectId, data.name, access);
        await onTokenCreated(); // Call the callback to refresh the token list
        return newToken;
    };

    const handleCopy = (token: string) => {
        navigator.clipboard
            .writeText(token)
            .then(() => {
                setIsCopied(true);
                setTimeout(() => setIsCopied(false), 2000); // Revert back after 2 seconds
            })
            .catch((err) => {
                console.error("Failed to copy token: ", err);
            });
    };

    const renderForm = (data: any, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new token</h2>
            <Input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
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
            <div className="bg-muted flex items-center p-2 rounded justify-between">
                <pre className="m-1">
                    <code>{data.token}</code>
                </pre>
                <button
                    onClick={() => handleCopy(data.token)}
                    className="ml-2 px-4 py-2 rounded text-gray-500 hover:text-gray-700"
                >
                    {isCopied ? (
                        <div className="flex justify-between">
                            <ClipboardCheck />
                            <p>Copied</p>
                        </div>
                    ) : (
                        <ClipboardCopy />
                    )}
                </button>
            </div>
            <p className="text-l mb-4 p-2">
                Make sure to copy the token above as it will not be shown again.
                We don&apos;t store it for security reasons.
            </p>
        </div>
    );
    return (
        <GeneralModal
            isOpen={isOpen}
            onClose={onClose}
            onSave={handleSave}
            initialData={initialData}
            initialSavedData={initialSavedData}
            renderForm={renderForm}
            renderSavedData={renderSavedData}
        />
    );
};

export default ProjectTokenModal;
