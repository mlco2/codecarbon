"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ProjectTokensTable } from "../../../../../../components/projectTokens/projectTokenTable";
import { use, useEffect, useState } from "react";
import { getOneProject, updateProject } from "@/server-functions/projects";
import { Project } from "@/types/project";

export default function ProjectSettingsPage({
    params,
}: {
    params: Promise<{ projectId: string }>;
}) {
    const { projectId } = use(params);

    const [project, setProject] = useState({
        name: "Project Name",
        description: "Project Description",
    });

    const [saveSuccess, setSaveSuccess] = useState(false);

    useEffect(() => {
        const fetchProject = async () => {
            // Fetch the project details from the API
            const response: Project = await getOneProject(projectId);
            setProject(response);
        };
        fetchProject();
    }, [projectId]);

    const handleClick = async () => {
        try {
            // Update the project details
            await updateProject(projectId, project);
            setSaveSuccess(true);
        } catch (error) {
            setSaveSuccess(false);
        } finally {
            setTimeout(() => setSaveSuccess(false), 3000); // Hide the success message after 3 seconds
        }
    };

    return (
        <div className="flex px-4 space-y-6 md:px-6 flex-col">
            <div className="space-y-1.5">
                <div className="flex items-center space-x-4">
                    <div className="space-y-1.5">
                        <h1 className="text-2xl font-bold">Settings</h1>
                        <p className="font-semi-bold">Project Settings</p>
                    </div>
                </div>
            </div>
            <div className="flex">
                <main className="flex-1 p-4 md:p-8">
                    <h1 className="text-2xl font-semi-bold">General</h1>
                    <div className="flex-1 p-4 md:p-8">
                        <section className="px-4 space-y-6 md:px-6">
                            <div className="space-y-4">
                                <div className="max-w-md">
                                    <div>
                                        <Label htmlFor="project-name">
                                            Project Name
                                        </Label>
                                        <Input
                                            id="project-name"
                                            placeholder="Enter project name"
                                            className="mt-1 w-full"
                                            value={project.name}
                                            onChange={(e) =>
                                                setProject({
                                                    ...project,
                                                    name: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                </div>
                                <div className="max-w-md">
                                    <div>
                                        <Label htmlFor="project-description">
                                            Project Description
                                        </Label>
                                        <Input
                                            id="project-description"
                                            placeholder="Enter project description"
                                            className="mt-1 w-full"
                                            value={project.description}
                                            onChange={(e) =>
                                                setProject({
                                                    ...project,
                                                    description: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-start p-4 mt-6 pr-8">
                                <Button variant="default" onClick={handleClick}>
                                    Save Changes
                                </Button>
                                {saveSuccess && (
                                    <p className="text-primary-foreground1 ml-4">
                                        ✓ Changes saved successfully!
                                    </p>
                                )}
                            </div>
                        </section>
                    </div>
                    <h1 className="p-4 text-2xl font-semi-bold">API tokens</h1>
                    <section className="px-4 md:px-6">
                        <ProjectTokensTable projectId={projectId} />
                    </section>
                </main>
            </div>
        </div>
    );
}
