"use client";

import { useState } from "react";
import { User } from "@/types/user";
import CustomRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody } from "@/components/ui/table";
import { addUser } from "@/server-functions/users";
import { useRouter } from "next/navigation";

interface MembersListProps {
    users: User[];
    organizationId: string;
}

export default function MembersList({
    users,
    organizationId,
}: MembersListProps) {
    const [isDialogOpen, setDialogOpen] = useState(false);
    const [email, setEmail] = useState("");
    const router = useRouter();

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
                    <div className="flex flex-col gap-4 rounded-md border-[0.5px] border-white p-4">
                        <h2>Add member</h2>
                        <Input
                            id="emailInput"
                            placeholder="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                        <div className="flex justify-end gap-6">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setEmail("");
                                    setDialogOpen(false);
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={async () => {
                                    if (!email) {
                                        alert("Please enter an email");
                                        return;
                                    }
                                    await addUser(organizationId, email);
                                    setDialogOpen(false);
                                    router.refresh();
                                }}
                            >
                                Ok
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
                                .map((user) => (
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
