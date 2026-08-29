import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { AccessLevel, IProjectToken } from "@/api/schemas";
import { getProjectTokens, createProjectToken } from "@/api/projectTokens";
import CustomRowToken from "@/components/projectTokens/custom-row-token";
import { useMemo, useState, useEffect, useRef } from "react";
import { Loader2, ClipboardCopy, ClipboardCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "@/components/icons/plus-icon";
import { FormField } from "@/components/ui/form-field";
import { PrimaryButton } from "@/components/ui/primary-button";
import { SecondaryButton } from "@/components/ui/secondary-button";
import { toast } from "sonner";
import copy from "copy-to-clipboard";

export const ProjectTokensTable = ({ projectId }: { projectId: string }) => {
    const [tokens, setTokens] = useState<IProjectToken[] | null>(null);
    const [isCreatingToken, setIsCreatingToken] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [tokenName, setTokenName] = useState("");
    const [createdToken, setCreatedToken] = useState<string | null>(null);
    const [isCopied, setIsCopied] = useState(false);
    const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    useEffect(() => {
        return () => {
            if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
        };
    }, []);
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
    };

    const handleCreateToken = async () => {
        if (!tokenName.trim()) return;
        if (isSubmitting) return;

        setIsSubmitting(true);
        try {
            const newToken = await createProjectToken(
                projectId,
                tokenName,
                AccessLevel.WRITE,
            );
            toast.success(`Token ${tokenName} created successfully`);
            setCreatedToken(newToken.token ?? null);
            setTokenName("");
            refreshTokens();
        } catch (error) {
            console.error("Failed to create token:", error);
            toast.error(
                `Failed to create token: ${error instanceof Error ? error.message : "Unknown error"}`,
            );
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
                copyTimerRef.current = setTimeout(
                    () => setIsCopied(false),
                    2000,
                );
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

    const sortedTokens = useMemo(
        () =>
            tokens
                ? tokens
                      .slice()
                      .sort((a, b) =>
                          (a.name ?? "")
                              .toLowerCase()
                              .localeCompare((b.name ?? "").toLowerCase()),
                      )
                : null,
        [tokens],
    );

    return (
        <div className="flex-col p-4 md:gap-8 md:p-4 justify-between">
            <div className="flex-1 mb-8">
                {!isCreatingToken && !createdToken ? (
                    /* The table itself is not restyled yet; the controls around
                       it follow the redesign. */
                    <PrimaryButton
                        onClick={() => setIsCreatingToken(true)}
                        className="gap-4"
                    >
                        <PlusIcon className="size-5 shrink-0" />
                        Create a new token
                    </PrimaryButton>
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
                                aria-label="Copy token to clipboard"
                                className="ml-2 px-4 py-2 rounded text-muted-foreground hover:text-foreground"
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
                            shown again. We don&apos;t store it for security
                            reasons.
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
                        {/* A real form, so Enter submits. The field and the two
                            actions share a row from `sm` and stack below it. */}
                        <form
                            className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-2"
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleCreateToken();
                            }}
                        >
                            <FormField
                                id="token-name"
                                label="Token name"
                                hideLabel
                                placeholder="Token name"
                                required
                                value={tokenName}
                                onChange={(e) => setTokenName(e.target.value)}
                                disabled={isSubmitting}
                                containerClassName="min-w-0 flex-1"
                            />
                            <div className="flex shrink-0 gap-2">
                                <PrimaryButton
                                    type="submit"
                                    disabled={isSubmitting || !tokenName.trim()}
                                >
                                    {isSubmitting && (
                                        <Loader2 className="size-4 animate-spin motion-reduce:animate-none" />
                                    )}
                                    {isSubmitting ? "Creating..." : "Create"}
                                </PrimaryButton>
                                <SecondaryButton
                                    onClick={() => setIsCreatingToken(false)}
                                    disabled={isSubmitting}
                                >
                                    Cancel
                                </SecondaryButton>
                            </div>
                        </form>
                    </Card>
                )}
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {sortedTokens === null ? (
                            <tr>
                                <td colSpan={3} className="text-center py-6">
                                    <div className="flex justify-center">
                                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                    </div>
                                </td>
                            </tr>
                        ) : sortedTokens.length === 0 ? (
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
                            sortedTokens.map((projectToken) => (
                                <CustomRowToken
                                    key={projectToken.id}
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
