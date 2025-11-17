import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { getOneProject, updateProject } from "@/server-functions/projects";
import { Project } from "@/types/project";
import { revalidatePath } from "next/cache";
import { ProjectTokensTable } from "../../../../../../components/projectTokens/projectTokenTable";
import ShareProjectButton from "@/components/share-project-button";

// Server Action for updating project
async function updateProjectAction(projectId: string, formData: FormData) {
    "use server";

    const name = formData.get("name") as string;
    const description = formData.get("description") as string;
    const isPublic = formData.has("isPublic");

    await updateProject(projectId, {
        name,
        description,
        public: isPublic,
    });

    revalidatePath(`/projects/${projectId}/settings`);
}

export default async function ProjectSettingsPage({
    params,
}: {
    params: Promise<{ projectId: string }>;
}) {
    const { projectId } = await params;
    const project: Project | null = await getOneProject(projectId);

    if (!project) {
        return <div>Project not found</div>;
    }

    return (
        <div className="flex px-4 space-y-6 md:px-6 flex-col">
            <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                    <div className="space-y-1.5">
                        <h1 className="text-2xl font-bold">Settings</h1>
                        <p className="font-semi-bold">Project Settings</p>
                    </div>
                    <div>
                        <ShareProjectButton
                            projectId={projectId}
                            isPublic={project?.public}
                        />
                    </div>
                </div>
            </div>
            <div className="flex">
                <div className="flex-1 p-4 md:p-8">
                    <h1 className="text-2xl font-semi-bold">General</h1>
                    <div className="flex-1 p-4 md:p-8">
                        <section className="px-4 space-y-6 md:px-6">
                            <form
                                action={updateProjectAction.bind(
                                    null,
                                    projectId,
                                )}
                            >
                                <div className="space-y-4">
                                    <div className="max-w-md">
                                        <Label htmlFor="name">
                                            Project Name
                                        </Label>
                                        <Input
                                            id="name"
                                            name="name"
                                            placeholder="Enter project name"
                                            className="mt-1 w-full"
                                            defaultValue={project?.name}
                                        />
                                    </div>
                                    <div className="max-w-md">
                                        <Label htmlFor="description">
                                            Project Description
                                        </Label>
                                        <Input
                                            id="description"
                                            name="description"
                                            placeholder="Enter project description"
                                            className="mt-1 w-full"
                                            defaultValue={project?.description}
                                        />
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Switch
                                            id="isPublic"
                                            name="isPublic"
                                            defaultChecked={project?.public}
                                            value="true"
                                        />
                                        <Label htmlFor="isPublic">
                                            Make project public
                                        </Label>
                                        <p className="text-sm text-muted-foreground ml-2">
                                            (enables public sharing link)
                                        </p>
                                    </div>
                                </div>
                                <div className="flex justify-start p-4 mt-6 pr-8">
                                    <Button type="submit">Save Changes</Button>
                                </div>
                            </form>
                        </section>
                    </div>
                    <h1 className="p-4 text-2xl font-semi-bold">API tokens</h1>
                    <section className="px-4 md:px-6">
                        <ProjectTokensTable projectId={projectId} />
                    </section>
                </div>
            </div>
        </div>
    );
}
