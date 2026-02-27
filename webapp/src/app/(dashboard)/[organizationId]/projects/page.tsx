"use client";

import BreadcrumbHeader from "@/components/breadcrumb";
import CreateProjectModal from "@/components/createProjectModal";
import CustomRow from "@/components/custom-row";
import DeleteProjectModal from "@/components/delete-project-modal";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import { fetcher } from "@/helpers/swr";
import { REFRESH_INTERVAL_ONE_MINUTE } from "@/helpers/time-constants";
import { useModal } from "@/hooks/useModal";
import { getProjects, deleteProject } from "@/server-functions/projects";
import { Project } from "@/types/project";
import { use, useEffect, useState } from "react";
import useSWR from "swr";
import { toast } from "sonner";

export default function ProjectsPage({
    params,
}: {
    params: Promise<{ organizationId: string }>;
}) {
    const { organizationId } = use(params);
    const createModal = useModal();
    const deleteModal = useModal();
    const [projectList, setProjectList] = useState<Project[]>([]);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(
        null,
    );

    const handleClick = async () => {
        createModal.open();
    };

    const refreshProjectList = async () => {
        // Fetch the updated list of projects from the server
        const projectList = await getProjects(organizationId);
        setProjectList(projectList || []);
    };

    const handleDeleteClick = (project: Project) => {
        setProjectToDelete(project);
        deleteModal.open();
    };

    const handleDeleteConfirm = async (projectId: string) => {
        try {
            await deleteProject(projectId);
            toast.success("Project deleted successfully");
            await refreshProjectList();
        } catch (error) {
            console.error("Error deleting project:", error);
            toast.error("Failed to delete project");
        }
    };

    // Fetch the updated list of projects from the server
    const {
        data: projects,
        error,
        isLoading,
    } = useSWR<Project[]>(`/projects?organization=${organizationId}`, fetcher, {
        refreshInterval: REFRESH_INTERVAL_ONE_MINUTE,
    });

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
        <div>
            <BreadcrumbHeader
                pathSegments={[
                    {
                        title:
                            localStorage.getItem("organizationName") ||
                            organizationId,
                        href: `/${organizationId}`,
                    },
                    {
                        title: "Projects",
                        href: null,
                    },
                ]}
            />
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
                        organizationId={organizationId}
                        isOpen={createModal.isOpen}
                        onClose={createModal.close}
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
                                            .localeCompare(
                                                b.name.toLowerCase(),
                                            ),
                                    )
                                    .map((project) => (
                                        <CustomRow
                                            key={project.id}
                                            rowKey={project.id}
                                            firstColumn={project.name}
                                            secondColumn={project.description}
                                            href={`/${organizationId}/projects/${project.id}`}
                                            hrefSettings={`/${organizationId}/projects/${project.id}/settings`}
                                            settingsDisabled={false}
                                            deleteDisabled={false}
                                            onDelete={async () =>
                                                handleDeleteClick(project)
                                            }
                                        />
                                    ))}
                        </TableBody>
                    </Table>
                </Card>
                {projectToDelete && (
                    <DeleteProjectModal
                        open={deleteModal.isOpen}
                        onOpenChange={deleteModal.setIsOpen}
                        projectName={projectToDelete.name}
                        projectId={projectToDelete.id}
                        onDelete={handleDeleteConfirm}
                    />
                )}
            </div>
        </div>
    );
}
