"use client";

import { useState } from "react";
import { createExperiment } from "@/server-functions/experiments";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Experiment } from "@/types/experiment";
import GeneralModal from "./ui/modal";
import { Separator } from "./ui/separator";
import { ClipboardCheck, ClipboardCopy } from "lucide-react";

export default function CreateExperimentModal({
    projectId,
    isOpen,
    onClose,
    onExperimentCreated,
}: {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onExperimentCreated: () => void;
}) {
    const [isCopied, setIsCopied] = useState(false);
    const initialData: Experiment = {
        name: "",
        description: "",
        on_cloud: false,
        project_id: projectId,
    };
    const initialSavedData: Experiment = {
        project_id: projectId,
        name: "",
        description: "",
        on_cloud: false,
    };
    const handleSave = async (data: Experiment) => {
        const newExperiment: Experiment = await createExperiment(data);
        await onExperimentCreated(); // Call the callback to refresh the project list
        return newExperiment;
    };
    const handleCopy = (token: string | undefined) => {
        if (!token) return;
        navigator.clipboard
            .writeText(token)
            .then(() => {
                setIsCopied(true);
                setTimeout(() => setIsCopied(false), 2000); // Revert back after 2 seconds
            })
            .catch((err) => {
                console.error("Failed to copy experiment id: ", err);
            });
    };

    const renderForm = (data: Experiment, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new experiment</h2>
            <Separator className="mb-4" />
            <Input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                placeholder="Experiment Name"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.description}
                onChange={(e) =>
                    setData({ ...data, description: e.target.value })
                }
                placeholder="Experiment Description"
                className={"mt-4 mb-4"}
            />
        </div>
    );

    const renderSavedData = (data: Experiment, setSavedData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">
                Experiment {data.name} Created
            </h2>
            <Separator className="mb-4" />
            <p className="text-l mb-4">Id of this experiment:</p>
            <div className="bg-muted flex items-center p-2 rounded justify-between">
                <pre className="m-1">
                    <code>{data.id}</code>
                </pre>
                <button
                    onClick={() => handleCopy(data.id)}
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
}
