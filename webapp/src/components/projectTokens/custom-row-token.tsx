"use client";

import { IProjectToken } from "@/types/project";
import CustomRow from "../custom-row";
import { deleteProjectToken } from "@/server-functions/projectTokens";

export default function CustomRowToken({
    projectToken,
    onTokenDeleted,
}: {
    projectToken: IProjectToken;
    onTokenDeleted: () => void;
}) {
    const handleDelete = async (projectToken: IProjectToken) => {
        await deleteProjectToken(projectToken.project_id, projectToken.id);
        onTokenDeleted();
    };

    return (
        <CustomRow
            rowKey={projectToken.id}
            firstColumn={projectToken.name}
            secondColumn={projectToken.token}
            onDelete={() => handleDelete(projectToken)}
            deleteDisabled={false}
        />
    );
}
