"use client";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { IProjectToken } from "@/types/project";
import { getProjectTokens } from "@/server-functions/projectTokens";
import CreateTokenButton from "./createProjectTokenButton";
import CustomRowToken from "@/components/projectTokens/custom-row-token";
import { useState, useEffect } from "react";
export const ProjectTokensTable = ({ projectId }: { projectId: string }) => {
    const [tokens, setTokens] = useState<IProjectToken[]>([]);

    const fetchTokens = async () => {
        // Fetch the updated list of tokens from the server
        const projectTokens = await getProjectTokens(projectId);
        setTokens(projectTokens);
    };

    useEffect(() => {
        fetchTokens();
    }, []);

    return (
        <div className="flex-col p-4 md:gap-8 md:p-8 justify-between max-w-screen-sm">
            {/* <div className="flex justify-between items-center mb-4"> */}
            <div className="flex-1 p-4 md:p-4">
                <CreateTokenButton
                    projectId={projectId}
                    onTokenCreated={fetchTokens}
                />
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {Array.isArray(tokens) &&
                            tokens
                                .sort((a, b) =>
                                    a.name
                                        .toLowerCase()
                                        .localeCompare(b.name.toLowerCase()),
                                )
                                .map((projectToken, index) => (
                                    <CustomRowToken
                                        key={index}
                                        projectToken={projectToken}
                                        onTokenDeleted={fetchTokens}
                                    />
                                ))}
                    </TableBody>
                </Table>
            </Card>
        </div>
    );
};
