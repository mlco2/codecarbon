"use client";

import CustomRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody } from "@/components/ui/table";
import { User } from "@/types/user";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { z } from "zod";
import { toast } from "sonner";

export default function MembersList({
    users,
    organizationId,
}: {
    users: User[];
    organizationId: string;
}) {
    const router = useRouter();
    const [isDialogOpen, setDialogOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const form = { email: undefined };

    const emailSchema = z.object({
        email: z.string().email("Please enter a valid email address"),
    });

    async function addUser() {
        try {
            setIsLoading(true);
            const email = (
                document.getElementById("emailInput") as HTMLInputElement
            ).value;

            // Validate email
            emailSchema.parse({ email });
            setError(null);

            const body = JSON.stringify({ email });

            await toast
                .promise(
                    fetch(
                        `${process.env.NEXT_PUBLIC_API_URL}/organizations/${organizationId}/add-user`,
                        {
                            method: "POST",
                            headers: {
                                Accept: "application/json",
                                "Content-Type": "application/json",
                            },
                            body: body,
                        },
                    ).then(async (result) => {
                        const data = await result.json();
                        if (result.status !== 200) {
                            const errorObject = data.detail;
                            let errorMessage = "Failed to add user";

                            if (
                                Array.isArray(errorObject) &&
                                errorObject.length > 0
                            ) {
                                errorMessage = errorObject
                                    .map((error: any) => error.msg)
                                    .join("\n");
                            } else if (errorObject) {
                                errorMessage = JSON.stringify(errorObject);
                            }

                            throw new Error(errorMessage);
                        }
                        return data;
                    }),
                    {
                        loading: `Adding user ${email}...`,
                        success: `User ${email} added successfully`,
                        error: (err) => `${err.message}`,
                    },
                )
                .unwrap();

            // On success
            router.refresh();
            setDialogOpen(false);
        } catch (err) {
            if (err instanceof z.ZodError) {
                setError(err.errors[0].message);
            } else {
                setError(
                    err instanceof Error ? err.message : "An error occurred",
                );
            }
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div>
            <div className="container mx-auto p-4 md:gap-8 md:p-8">
                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-2xl font-semi-bold">Members</h1>
                    <Button
                        disabled={isDialogOpen}
                        onClick={() => setDialogOpen(true)}
                    >
                        + Add a member
                    </Button>
                </div>
                <div id="addMemberModalTarget"></div>
                {isDialogOpen && (
                    <div className="flex flex-col gap-2 mb-6 p-6 rounded-md border border-white/30">
                        <h2>Add member</h2>
                        <Input
                            id="emailInput"
                            placeholder="email"
                            value={form.email}
                        />
                        {error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                        <div className="flex justify-end gap-6">
                            <Button
                                disabled={isLoading}
                                variant="outline"
                                onClick={() => {
                                    form.email = undefined;
                                    setDialogOpen(false);
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={() => addUser()}
                                disabled={isLoading}
                            >
                                {isLoading ? "Adding..." : "Ok"}
                            </Button>
                        </div>
                    </div>
                )}
                <Card>
                    <Table>
                        <TableBody>
                            {users
                                .sort((a, b) =>
                                    a.name
                                        .toLowerCase()
                                        .localeCompare(b.name.toLowerCase()),
                                )
                                .map((user, index) => (
                                    <CustomRow
                                        key={user.id}
                                        rowKey={user.id}
                                        firstColumn={user.name}
                                        secondColumn={user.email}
                                    />
                                ))}
                        </TableBody>
                    </Table>
                </Card>
            </div>
        </div>
    );
}
