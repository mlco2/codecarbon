"use client";

import CustomRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { Project } from "@/types/project";

/**
 * Retrieves the list of projects for a given organization
 * @param organizationId comes from the URL parameters
 */
async function fetchProjects(organizationId: string): Promise<Project[]> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects?organization=${organizationId}`,
    );

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }

    return res.json();
}

export default async function ProjectsPage({
    params,
}: Readonly<{ params: { organizationId: string } }>) {
    const projects = await fetchProjects(params.organizationId);
    console.log("ProjectsPage: fetchProjects", projects.length);

    return (
        <div className="container mx-auto p-4 md:gap-8 md:p-8">
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-semi-bold">Projects</h1>
                <Button disabled className="bg-primary text-primary-foreground">
                    + Add a project
                </Button>
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {projects
                            .sort((a, b) =>
                                a.name
                                    .toLowerCase()
                                    .localeCompare(b.name.toLowerCase()),
                            )
                            .map((project) => (
                                <CustomRow
                                    key={project.id}
                                    firstColumn={project.name}
                                    secondColumn={project.description}
                                    href={`/${params.organizationId}/projects/${project.id}`}
                                />
                            ))}
                    </TableBody>
                </Table>
            </Card>
        </div>
    );
}
