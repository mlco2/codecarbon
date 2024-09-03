"use server";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Card } from "@/components/ui/card";
import { Table, TableBody } from "@/components/ui/table";
import CustomRow from "@/components/custom-row";
import { IProjectToken } from "@/types/project";
import { getProjectTokens } from "@/server-functions/projectTokens";
import CreateTokenButton from "./createProjectTokenButton";

const ProjectTokensTable = ({
    projectTokens,
    projectId,
}: {
    projectTokens: IProjectToken[];
    projectId: string;
}) => {
    return (
        <div className="container mx-auto p-4 md:gap-8 md:p-8">
            {/* <div className="flex justify-between items-center mb-4"> */}
            <div className="flex-1 p-4 md:p-8">
                <CreateTokenButton projectId={projectId} />
            </div>
            <Card>
                <Table>
                    <TableBody>
                        {projectTokens
                            .sort((a, b) =>
                                a.name
                                    .toLowerCase()
                                    .localeCompare(b.name.toLowerCase())
                            )
                            .map((projectToken, index) => (
                                <CustomRow
                                    key={projectToken.id}
                                    firstColumn={projectToken.name}
                                    secondColumn={projectToken.token}
                                />
                            ))}
                    </TableBody>
                </Table>
            </Card>
        </div>
    );
};

export default async function ProjectSettingsPage({
    params,
}: Readonly<{ params: { projectId: string } }>) {
    // Get the projectId from the URL
    const projectId = params.projectId;

    const projectTokens = await getProjectTokens(projectId);
    console.log("ProjectSettingsPage: tokens", projectTokens);
    console.log("ProjectSettingsPage: getProjectTokens", projectTokens.length);

    return (
        <div className="flex px-4 space-y-6 md:px-6 flex-col">
            <div className="space-y-1.5">
                <div className="flex items-center space-x-4">
                    <div className="space-y-1.5">
                        <h1 className="text-2xl font-bold">Settings</h1>
                        <p className="text-gray-500 dark:text-gray-400">
                            Project Settings
                        </p>
                    </div>
                </div>
            </div>
            <div className="flex">
                <main className="flex-1 p-4 md:p-8">
                    <h1 className="text-2xl font-semi-bold">General</h1>
                    <div className="flex-1 p-4 md:p-8">
                        <section className="px-4 space-y-6 md:px-6">
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="project-name">
                                        Project Name
                                    </Label>
                                    <Input
                                        id="project-name"
                                        placeholder="Enter project name"
                                        className="mt-1"
                                        disabled
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="project-description">
                                        Project Description
                                    </Label>
                                    <Input
                                        id="project-description"
                                        placeholder="Enter project description"
                                        className="mt-1"
                                        disabled
                                    />
                                </div>
                            </div>
                        </section>
                        <div className="flex justify-end p-4 mt-6 pr-8">
                            <Button variant="default" disabled>
                                Save Changes
                            </Button>
                        </div>
                    </div>
                    <h1 className="p-4 text-2xl font-semi-bold">API tokens</h1>
                    <div className="flex-1 p-4 md:p-8"></div>
                    <ProjectTokensTable
                        projectTokens={projectTokens}
                        projectId={projectId}
                    />
                </main>
            </div>
        </div>
    );
}
