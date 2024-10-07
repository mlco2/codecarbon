"use client";

import { IProjectToken } from "@/types/project";
import CustomRow from "../custom-row";
import { deleteProjectToken } from "@/server-functions/projectTokens";

export default function CustomRowToken({
    projectToken,
    onTokenDeleted,
}: {
    projectToken: IProjectToken;
    onTokenDeleted: () => Promise<void>;
}) {
    const handleDelete = async (projectToken: IProjectToken) => {
        await deleteProjectToken(projectToken.project_id, projectToken.id);
        await onTokenDeleted(); // Call the callback to refresh the token list
    };

    return (
        <CustomRow
            key={projectToken.id}
            firstColumn={projectToken.name}
            secondColumn={projectToken.token}
            onDelete={() => handleDelete(projectToken)}
            deleteDisabled={false}
        />
    );
}
