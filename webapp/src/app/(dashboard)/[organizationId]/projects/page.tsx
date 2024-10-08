"use client";

import CustomRow from "@/components/custom-row";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { fetcher } from "@/helpers/swr";
import { Project } from "@/types/project";
import useSWR from "swr";

export default function ProjectsPage({
    params,
}: Readonly<{ params: { organizationId: string } }>) {
    const {
        data: projects,
        error,
        isLoading,
    } = useSWR<Project[]>(
        `/projects?organization=${params.organizationId}`,
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
                        {projects &&
                            projects
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
                                        hrefSettings={`/${params.organizationId}/projects/${project.id}/settings`}
                                        settingsDisabled={false}
                                    />
                                ))}
                    </TableBody>
                </Table>
            </Card>
        </div>
    );
}
