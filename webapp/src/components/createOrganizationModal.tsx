import GeneralModal from "./ui/modal";
import { createOrganization } from "@/server-functions/organizations";
import { Separator } from "./ui/separator";
import { Input } from "./ui/input";
import { Organization } from "@/types/organization";

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
    const initialData: CreateOrganizationInput = {
        name: "",
        description: "",
    };
    const initialSavedData: Organization = {
        name: "",
        id: "",
        description: "",
    };
    const handleSave = async (data: CreateOrganizationInput) => {
        const newOrganization: Organization | null =
            await createOrganization(data);
        if (newOrganization) {
            await onOrganizationCreated(); // Call the callback to refresh the project list
            return newOrganization;
        }
        return null;
    };

    const renderForm = (data: CreateOrganizationInput, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new organization</h2>
            <Separator className="mb-4" />
            <Input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                placeholder="Organization Name"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.description}
                onChange={(e) =>
                    setData({ ...data, description: e.target.value })
                }
                placeholder="Organization Description"
                className={"mt-4 mb-4"}
            />
        </div>
    );
    const renderSavedData = (data: Organization, setSavedData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">
                Organization {data.name} Created
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

export default CreateOrganizationModal;
