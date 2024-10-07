"use client";

import useSWR from "swr";
import { Activity, CreditCard, Users } from "lucide-react";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Project } from "@/types/project";
import { fetcher } from "../../../../../helpers/swr";
import Loader from "@/components/loader";
import ErrorMessage from "@/components/error-message";
import { useRouter } from "next/navigation";
import { SettingsIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function ProjectPage({
    params,
}: Readonly<{
    params: {
        projectId: string;
        organizationId: string;
    };
}>) {
    const router = useRouter();
    const handleSettingsClick = () => {
        router.push(
            `/${params.organizationId}/projects/${params.projectId}/settings`,
        );
    };
    const {
        data: project,
        isLoading,
        error,
    } = useSWR<Project>(`/projects/${params.projectId}`, fetcher, {
        refreshInterval: 1000 * 60, // Refresh every minute
    });
    if (isLoading) {
        return <Loader />;
    }

    if (error) {
        return <ErrorMessage />;
    }

    if (project) {
        return (
            <div className="h-full w-full overflow-auto">
                <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-semi-bold">
                            {project.name}
                        </h1>
                        <Button
                            onClick={handleSettingsClick}
                            variant="ghost"
                            size="icon"
                            className="rounded-full"
                        >
                            <SettingsIcon className="mr-2 h-4 w-4" />
                            Settings
                        </Button>
                    </div>
                    <span className="text-sm font-semi-bold">
                        {project.description}
                    </span>
                    <Separator className="h-[0.5px] bg-muted-foreground" />
                    <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
                        <Card x-chunk="A card showing the total subscriptions and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">
                                    Emissions of the project
                                </CardTitle>
                                <Users className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-muted-foreground">
                                    5.45 kgCO2 equivalent
                                </p>
                            </CardContent>
                        </Card>
                        <Card x-chunk="A card showing the total sales and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium"></CardTitle>
                                <Activity className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    Over 3 experiments
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    +19% from last month
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2 md:gap-8">
                        <ExperimentsBarChart
                            params={{ projectId: project.id }}
                        />
                        <RunsScatterChart
                            params={{ experimentId: project.experiments[1] }}
                        />
                    </div>
                </main>
            </div>
        );
    }
}
