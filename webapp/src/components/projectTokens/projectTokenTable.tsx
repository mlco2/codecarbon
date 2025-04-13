"use client";

import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { IProjectToken } from "@/types/project";
import {
    getProjectTokens,
    createProjectToken,
} from "@/server-functions/projectTokens";
import CustomRowToken from "@/components/projectTokens/custom-row-token";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ClipboardCopy, ClipboardCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import copy from "copy-to-clipboard";

export const ProjectTokensTable = ({ projectId }: { projectId: string }) => {
    const [tokens, setTokens] = useState<IProjectToken[] | null>(null);
    const [isCreatingToken, setIsCreatingToken] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [tokenName, setTokenName] = useState("");
    const [createdToken, setCreatedToken] = useState<string | null>(null);
    const [isCopied, setIsCopied] = useState(false);
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

    const handleCreateToken = async () => {
        if (!tokenName.trim()) return;
        if (isSubmitting) return;

        setIsSubmitting(true);

        try {
            const access = 2;
            const newToken = await toast
                .promise(createProjectToken(projectId, tokenName, access), {
                    loading: `Creating token ${tokenName}...`,
                    success: `Token ${tokenName} created successfully`,
                    error: (error) =>
                        `Failed to create token: ${error instanceof Error ? error.message : "Unknown error"}`,
                })
                .unwrap();

            setCreatedToken(newToken.token);
            setTokenName("");
            refreshTokens();
        } catch (error) {
            console.error("Failed to create token:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCopy = (token: string) => {
        try {
            const success = copy(token);
            if (success) {
                setIsCopied(true);
                toast.success("Token copied to clipboard");
                setTimeout(() => setIsCopied(false), 2000); // Revert back after 2 seconds
            } else {
                throw new Error("Copy operation failed");
            }
        } catch (err) {
            toast.error("Failed to copy token to clipboard");
            console.error("Failed to copy token: ", err);
        }
    };

    const resetTokenCreation = () => {
        setCreatedToken(null);
        setIsCreatingToken(false);
    };

    return (
        <div className="flex-col p-4 md:gap-8 md:p-4 justify-between">
            <div className="flex-1 mb-4">
                {!isCreatingToken && !createdToken ? (
                    <Button
                        className="bg-primary text-primary-foreground"
                        onClick={() => setIsCreatingToken(true)}
                    >
                        + Create a new token
                    </Button>
                ) : createdToken ? (
                    <Card className="p-4 mb-4">
                        <h2 className="text-xl font-bold mb-4">
                            Token Created
                        </h2>
                        <p className="text-l mb-4">
                            The following token has been generated:
                        </p>
                        <div className="bg-muted flex items-center p-2 rounded justify-between">
                            <pre className="m-1">
                                <code>{createdToken}</code>
                            </pre>
                            <button
                                onClick={() => handleCopy(createdToken)}
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
                        <p className="text-l mt-4 p-2">
                            Make sure to copy the token above as it will not be
                            shown again. We&apos;ll don&apos;t store it for
                            security reasons.
                        </p>
                        <Button onClick={resetTokenCreation} className="mt-4">
                            Done
                        </Button>
                    </Card>
                ) : (
                    <Card className="p-4 mb-4">
                        <h2 className="text-xl font-bold mb-4">
                            Create new token
                        </h2>
                        <div className="flex gap-2">
                            <Input
                                type="text"
                                value={tokenName}
                                onChange={(e) => setTokenName(e.target.value)}
                                placeholder="Token Name"
                                className="flex-grow"
                                disabled={isSubmitting}
                            />
                            <Button
                                onClick={handleCreateToken}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Create"
                                )}
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setIsCreatingToken(false)}
                                disabled={isSubmitting}
                            >
                                Cancel
                            </Button>
                        </div>
                    </Card>
                )}
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
                                    <p className="text-muted-foreground">
                                        No API tokens found
                                    </p>
                                    <p className="text-sm text-muted-foreground mt-2">
                                        Create a token to interact with the
                                        CodeCarbon API
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
