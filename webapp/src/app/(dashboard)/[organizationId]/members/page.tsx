import CustomRow from "@/components/custom-row";
import ProjectRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { Project } from "@/types/project";
import { User } from "@/types/user";

/**
 * Retrieves the list of users for a given organization
 * @TODO Filer per organizationId when the endpoint is ready.
 * @param organizationId comes from the URL parameters
 */
async function fetchUsersByOrg(organizationId: string): Promise<User[]> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/users?organization=${organizationId}`,
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

export default async function MembersPage({
    params,
}: Readonly<{ params: { organizationId: string } }>) {
    const users = await fetchUsersByOrg(params.organizationId);

    return (
        <div className="container mx-auto p-4 md:gap-8 md:p-8">
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-semi-bold">Members</h1>
                <Button disabled className="bg-primary text-primary-foreground">
                    + Add a member
                </Button>
            </div>
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
    );
}
