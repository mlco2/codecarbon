"use client";
import CustomRow from "@/components/custom-row";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody } from "@/components/ui/table";
import { User } from "@/types/user";
import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "../../../../helpers/swr";

export default function MembersList({
    users,
    organizationId,
}: {
    users: User[];
    organizationId: string;
}) {
    const [isDialogOpen, setDialogOpen] = useState(false);
    const { data, isLoading, error } = useSWR<User[]>(
        `/organizations/${organizationId}/users`,
        fetcher,
        {
            refreshInterval: 1000 * 60, // Refresh every minute
        },
    );
    if (isLoading) {
        return <Loader />;
    }
    if (error) {
        return <ErrorMessage />;
    }

    users = data as User[];
    const form = { email: undefined };

    async function addUser() {
        const body = JSON.stringify({
            email: (document.getElementById("emailInput") as any).value,
        });
        const result = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/organizations/${organizationId}/add-user`,
            {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: body,
            },
        );
        const data = await result.json();
        if (result.status != 200) {
            alert(data.detail);
        }
        setDialogOpen(false);
    }

    return (
        <div>
            <div className="container mx-auto p-4 md:gap-8 md:p-8">
                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-2xl font-semi-bold">Members</h1>
                    <Button onClick={() => setDialogOpen(true)}>
                        + Add a member
                    </Button>
                </div>
                <div id="addMemberModalTarget"></div>
                {isDialogOpen && (
                    <div className="flex flex-col gap-2 m-2 p-2 rounded-md border border-white">
                        <h2>Add member</h2>
                        <Input
                            id="emailInput"
                            placeholder="email"
                            value={form.email}
                        />
                        <div className="flex justify-end gap-6">
                            <Button
                                onClick={() => {
                                    form.email = undefined;
                                    setDialogOpen(false);
                                }}
                            >
                                Cancel
                            </Button>
                            <Button onClick={() => addUser()}>Ok</Button>
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
