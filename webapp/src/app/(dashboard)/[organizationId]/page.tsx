"use client";

import { Activity, CreditCard, DollarSign, Users } from "lucide-react";

import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { fetcher } from "@/helpers/swr";
import { Organization } from "@/types/organization";
import useSWR from "swr";

export default function OrganizationPage({
    params,
}: {
    params: { organizationId: string };
}) {
    const {
        data: organization,
        isLoading,
        error,
    } = useSWR<Organization>(
        `/organizations/${params.organizationId}`,
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
        <div className="h-full w-full overflow-auto">
            {!organization && <ErrorMessage />}
            {organization && (
                <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                    <h1 className="text-2xl font-semi-bold">
                        {organization.name} report
                    </h1>
                    <span className="text-sm font-semi-bold">
                        This section has the impact of all projects combined,
                        equivalent of
                    </span>
                    <Separator className="h-[0.5px] bg-muted-foreground" />
                    <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
                        <Card x-chunk="A card showing the total revenue in USD and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">
                                    Total emissions
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    15.93 kgCO2 equivalent
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    or around 288.44 MWh
                                </p>
                            </CardContent>
                        </Card>
                        <Card x-chunk="A card showing the total subscriptions and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium"></CardTitle>
                                <Users className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-muted-foreground">
                                    21.43% of an american Household weekly
                                    energy consumption
                                </p>
                            </CardContent>
                        </Card>
                        <Card x-chunk="A card showing the total sales and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium"></CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-muted-foreground">
                                    123 km driven
                                </p>
                            </CardContent>
                        </Card>
                        <Card x-chunk="A card showing the total active users and the percentage difference from last hour.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium"></CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-muted-foreground">
                                    14 days of TV
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </main>
            )}
        </div>
    );
}
