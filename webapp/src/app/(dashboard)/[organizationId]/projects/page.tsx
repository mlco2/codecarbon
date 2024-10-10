"use client";

import CreateProjectModal from "@/components/createProjectModal";
import CustomRow from "@/components/custom-row";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { fetcher } from "@/helpers/swr";
import { getProjects } from "@/server-functions/projects";
import { Project } from "@/types/project";
import { use, useEffect, useState } from "react";
import useSWR from "swr";

export default function ProjectsPage({
    params,
}: Readonly<{ params: { organizationId: string } }>) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [projectList, setProjectList] = useState<Project[]>([]);
    const handleClick = async () => {
        setIsModalOpen(true);
    };
    const refreshProjectList = async () => {
        // Fetch the updated list of projects from the server
        const projectList = await getProjects(params.organizationId);
        setProjectList(projectList);
    };
    // Fetch the updated list of projects from the server
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

    useEffect(() => {
        if (projects) {
            setProjectList(projects);
        }
    }, [projects]);
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
                <Button
                    onClick={handleClick}
                    className="bg-primary text-primary-foreground"
                >
                    + Add a project
                </Button>
                <CreateProjectModal
                    organizationId={params.organizationId}
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onProjectCreated={refreshProjectList}
                />
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {projectList &&
                            projectList
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
