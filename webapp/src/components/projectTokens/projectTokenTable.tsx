"use client";

import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { IProjectToken } from "@/types/project";
import { getProjectTokens } from "@/server-functions/projectTokens";
import CreateTokenButton from "./createProjectTokenButton";
import CustomRowToken from "@/components/projectTokens/custom-row-token";
import { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export const ProjectTokensTable = ({ projectId }: { projectId: string }) => {
    const [tokens, setTokens] = useState<IProjectToken[] | null>(null);
    const router = useRouter();

    useEffect(() => {
        const fetchTokens = async () => {
            // Fetch the updated list of tokens from the server
            const projectTokens = await getProjectTokens(projectId);
            setTokens(projectTokens);
        };
        if (tokens === null) {
            fetchTokens();
        }
    }, [projectId, tokens]);

    const refreshTokens = () => {
        setTokens(null); // This will trigger a refetch in the useEffect
        router.refresh(); // Refresh the current route
    };

    return (
        <div className="flex-col p-4 md:gap-8 md:p-4 justify-between">
            <div className="flex-1 mb-4">
                <CreateTokenButton
                    projectId={projectId}
                    onTokenCreated={refreshTokens}
                />
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {tokens === null ? (
                            <tr>
                                <td colSpan={3} className="text-center py-6">
                                    <div className="flex justify-center">
                                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                    </div>
                                </td>
                            </tr>
                        ) : tokens.length === 0 ? (
                            <tr>
                                <td colSpan={3} className="text-center py-6">
                                    <p className="text-muted-foreground">No API tokens found</p>
                                    <p className="text-sm text-muted-foreground mt-2">
                                        Create a token to interact with the CodeCarbon API
                                    </p>
                                </td>
                            </tr>
                        ) : (
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
                                        onTokenDeleted={refreshTokens}
                                    />
                                ))
                        )}
                    </TableBody>
                </Table>
            </Card>
        </div>
    );
};
