"use client";

import { Activity, CreditCard, DollarSign, Users } from "lucide-react";

import ErrorMessage from "@/components/error-message";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Organization } from "@/types/organization";
import useSWR from "swr";
import { fetcher } from "@/helpers/swr";
import { Skeleton } from "@/components/ui/skeleton";

// /**
//  * Retrieves an organization based on the id
//  */
// async function getOrganization(orgId: string): Promise<Organization | null> {
//     try {
//         const res = await fetch(
//             `${process.env.NEXT_PUBLIC_API_URL}/organizations/${orgId}`
//         );

//         if (!res.ok) {
//             // This will activate the closest `error.js` Error Boundary
//             throw new Error("Failed to fetch data");
//         }

//         return res.json();
//     } catch (error) {
//         if (error instanceof Error) {
//             console.error("Error fetching organization:", error.message);
//         }
//         return null;
//     }
// }

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
        `/api/organizations/${params.organizationId}`,
        fetcher,
        {
            refreshInterval: 1000 * 60, // Refresh every minute
        }
    );

    if (isLoading) {
        return (
            <div className="flex items-center space-x-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2">
                    <Skeleton className="h-4 w-[250px]" />
                    <Skeleton className="h-4 w-[200px]" />
                </div>
            </div>
        );
    }

    if (error) {
        return <ErrorMessage />;
    }

    console.log(organization);

    return (
        <div className="h-full w-full overflow-auto">
            {!organization && <ErrorMessage />}
            {organization && (
                <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                    <h1 className="text-2xl font-semi-bold">
                        {organization.name}
                    </h1>
                    <span className="text-sm font-semi-bold">
                        {organization.description}
                    </span>
                    <Separator className="h-[0.5px] bg-muted-foreground" />
                    <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
                        <Card x-chunk="A card showing the total revenue in USD and the percentage difference from last month.">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">
                                    Total Revenue
                                </CardTitle>
                                <DollarSign className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    $45,231.89
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    +20.1% from last month
                                </p>
                            </CardContent>
                        </Card>
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
                                <div className="text-2xl font-bold">
                                    +12,234
                                </div>
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
                    </div>
                </main>
            )}
        </div>
    );
}
