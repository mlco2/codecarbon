"use client";
import { Button } from "@/components/ui/button";
import { createProjectToken } from "@/server-functions/projectTokens";

const CreateTokenButton = ({ projectId }: { projectId: string }) => {
    const handleClick = async () => {
        const tokenName = "tokenName";
        const access = 2;
        const newToken = await createProjectToken(projectId, tokenName, access);
        console.log("ProjectSettingsPage: createProjectToken", newToken);
    };

    return (
        <Button
            className="bg-primary text-primary-foreground"
            onClick={handleClick}
        >
            + Create a new token
        </Button>
    );
};

export default CreateTokenButton;
