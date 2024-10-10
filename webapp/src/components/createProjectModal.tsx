import { Project } from "@/types/project";
import GeneralModal from "./ui/modal";
import { createProject } from "@/server-functions/projects";
import { Separator } from "./ui/separator";
import { Input } from "./ui/input";

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
        await onProjectCreated(); // Call the callback to refresh the project list
        return newProject;
    };

    const renderForm = (data: CreateProjectInput, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new project</h2>
            <Separator className="mb-4" />
            <Input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                placeholder="Project Name"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.description}
                onChange={(e) =>
                    setData({ ...data, description: e.target.value })
                }
                placeholder="Project Description"
                className={"mt-4 mb-4"}
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
