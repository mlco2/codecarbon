"use client";
import CustomRow from "@/components/custom-row";
import ProjectRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { Project } from "@/types/project";
import { User } from "@/types/user";
import AddMember from "@/components/add-member"
import { useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher } from "../../../../helpers/swr";
import Loader from "@/components/loader";
import ErrorMessage from "@/components/error-message";
import { stringify } from "querystring";
import * as React from "react";
import * as Dialog from '@radix-ui/react-dialog';
import { Input } from "@/components/ui/input";
import { Text } from "lucide-react";
// import { Input } from "postcss";

/**
 * Retrieves the list of users for a given organization
 * @UNUSED
 * @TODO Filer per organizationId when the endpoint is ready.
 * @param organizationId comes from the URL parameters
 */
async function fetchUsersByOrg(organizationId: string): Promise<User[]> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/users?organization=${organizationId}`,
        {
            next: { revalidate: 60 }, // Revalidate every minute
        }
    );

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }
    return res.json();
}

export default function MembersPage({
    params,
}: Readonly<{ params: { organizationId: string } }>) {
    let users: User[] = [];
    const [isDialogOpen, setDialogOpen] = useState(false);
    const {
        data,
        isLoading,
        error,
    } = useSWR<User[]>(
        `/api/organizations/${params.organizationId}/users`,
        fetcher,
        {
            refreshInterval: 1000 * 60, // Refresh every minute
        }
    );
    if (isLoading) {
        return <Loader />;
    }
    if (error) {
        return <ErrorMessage />;
    }
    
    users = data as User[];
    const form = { email: undefined};

    async function addUser() {
        const body = JSON.stringify({
            email: (document.getElementById("emailInput") as any).value
        });
        const result = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/organizations/${params.organizationId}/add-user`, {
            method: "POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },            
            body: body,
        });
        const data = result.json();
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
                    <Button onClick={() => setDialogOpen(true)}>+ Add a member</Button>
                </div>
                <div id="addMemberModalTarget"></div>
                {isDialogOpen && <div style={{"margin": "2em", "borderRadius": "4px", "border": "1px solid white", padding: "1em"}}>
                    <h2>Add member</h2>
                        <br/>   
                        <Input id="emailInput" placeholder="email" value={form.email}/>
                        <br/>
                        <Button onClick={()=>{form.email=undefined;setDialogOpen(false)}}>Cancel</Button>
                        <Button onClick={()=>addUser()}>Ok</Button>
                </div>}
                <Card>
                    <Table>
                        <TableBody>
                            {users
                                .sort((a, b) =>
                                    a.name
                                        .toLowerCase()
                                        .localeCompare(b.name.toLowerCase())
                                )
                                .map((user, index) => (
                                    <CustomRow
                                        key={user.id}
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
