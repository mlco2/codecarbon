"use server";

import { Activity, CreditCard, Users } from "lucide-react";

import AreaChartStacked from "@/components/area-chart-stacked";
import BarChartMultiple from "@/components/bar-chart-multiple";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Project } from "@/types/project";

/**
 * Retrieves a project based on the projectId
 */
async function getProject(projectId: string): Promise<Project> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}`
    );

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }

    return res.json();
}

export default async function ProjectPage({
    params,
}: Readonly<{
    params: {
        projectId: string;
    };
}>) {
    const project = await getProject(params.projectId);

    return (
        <div className="h-full w-full overflow-auto">
            <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                <h1 className="text-2xl font-semi-bold">{project.name}</h1>
                <span className="text-sm font-semi-bold">
                    {project.description}
                </span>
                <Separator className="h-[0.5px] bg-muted-foreground" />
                <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
                    <Card x-chunk="A card showing the total subscriptions and the percentage difference from last month.">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Subscriptions
                            </CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">+2350</div>
                            <p className="text-xs text-muted-foreground">
                                +180.1% from last month
                            </p>
                        </CardContent>
                    </Card>
                    <Card x-chunk="A card showing the total sales and the percentage difference from last month.">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Sales
                            </CardTitle>
                            <CreditCard className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">+12,234</div>
                            <p className="text-xs text-muted-foreground">
                                +19% from last month
                            </p>
                        </CardContent>
                    </Card>
                    <Card x-chunk="A card showing the total active users and the percentage difference from last hour.">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Active Now
                            </CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">+573</div>
                            <p className="text-xs text-muted-foreground">
                                +201 since last hour
                            </p>
                        </CardContent>
                    </Card>
                    <Card x-chunk="A card showing the total active users and the percentage difference from last hour.">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Active Now
                            </CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">+573</div>
                            <p className="text-xs text-muted-foreground">
                                +201 since last hour
                            </p>
                        </CardContent>
                    </Card>
                </div>
                <div className="grid gap-4 md:grid-cols-2 md:gap-8">
                    <AreaChartStacked />
                    <BarChartMultiple />
                </div>
            </main>
        </div>
    );
}
