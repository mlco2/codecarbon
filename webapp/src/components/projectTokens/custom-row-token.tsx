"use client";

import { IProjectToken } from "@/types/project";
import CustomRow from "../custom-row";
import { deleteProjectToken } from "@/server-functions/projectTokens";
import { useState } from "react";
import { toast } from "sonner";

export default function CustomRowToken({
    projectToken,
    onTokenDeleted,
}: {
    projectToken: IProjectToken;
    onTokenDeleted: () => void;
}) {
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDelete = async (projectToken: IProjectToken) => {
        if (isDeleting) return;

        setIsDeleting(true);

        try {
            await toast
                .promise(
                    deleteProjectToken(
                        projectToken.project_id,
                        projectToken.id,
                    ),
                    {
                        loading: `Deleting token ${projectToken.name}...`,
                        success: `Token ${projectToken.name} deleted successfully`,
                        error: (error) =>
                            `Failed to delete token: ${error instanceof Error ? error.message : "Unknown error"}`,
                    },
                )
                .unwrap();
            onTokenDeleted();
        } catch (error) {
            console.error("Error deleting token:", error);
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <CustomRow
            rowKey={projectToken.id}
            firstColumn={projectToken.name}
            secondColumn={projectToken.token}
            onDelete={() => handleDelete(projectToken)}
            deleteDisabled={isDeleting}
        />
    );
}
