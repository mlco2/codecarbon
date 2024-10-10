import { IProjectToken, Project } from "@/types/project";
import React, { useState } from "react";
import { ClipboardCopy } from "lucide-react";
import GeneralModal from "./ui/modal";
import { createProject } from "@/server-functions/projects";

interface ModalProps {
    organizationId: string;
    isOpen: boolean;
    onClose: () => void;
}
interface CreateProjectInput {
    name: string;
    description: string;
}

const CreateProjectModal: React.FC<ModalProps> = ({
    organizationId,
    isOpen,
    onClose,
}) => {
    const initialData: CreateProjectInput = {
        name: "",
        description: "",
    };
    const initialSavedData: Project = {
        name: "",
        id: "",
        description: "",
        organizationId: "",
        experiments: [],
    };
    const handleSave = async (data: CreateProjectInput) => {
        const newProject: Project = await createProject(organizationId, data);
        return newProject;
    };

    const renderForm = (data: CreateProjectInput, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new project</h2>
            <input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                className="border p-2 w-full"
                placeholder="Project Name"
            />
            <input
                type="text"
                value={data.description}
                onChange={(e) =>
                    setData({ ...data, description: e.target.value })
                }
                className="border p-2 w-full"
                placeholder="Project Description"
            />
        </div>
    );
    const renderSavedData = (data: Project, setSavedData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">
                Project {data.name} Created
            </h2>
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

export default CreateProjectModal;
