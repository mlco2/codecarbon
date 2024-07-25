"use client";

import Loader from "@/components/loader";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetcher } from "@/helpers/swr";
import { Organization } from "@/types/organization";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR from "swr";

/**
 * Home Page with 4 different behaviors possible:
 * - Displays a loading spinner if the list of organizations is being queried
 * - A 'Get Started' guide if there is no data
 * - Redirects to the first organization dashboard
 * - Redirects to the user's last visited organization dashboard if any
 */
export default function HomePage() {
    const router = useRouter();
    const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    // Fetch the list of organizations to check if the account has data
    const { data: orgs, isLoading } = useSWR<Organization[]>(
        "/api/organizations",
        fetcher,
        {
            refreshInterval: 1000 * 60, // Refresh every minute
        }
    );

    useEffect(() => {
        if (!selectedOrg) {
            try {
                const localOrg = localStorage.getItem("organizationId");
                if (localOrg) {
                    setSelectedOrg(localOrg);
                } else if (orgs && orgs.length > 0) {
                    // Set the first organization as the default
                    setSelectedOrg(orgs[0].id);
                }
            } catch (error) {
                console.error("Error reading from localStorage:", error);
            }
            setLoading(false);
        }
    }, [selectedOrg, router, orgs]);

    useEffect(() => {
        if (selectedOrg) {
            router.push(`/${selectedOrg}`);
        }
    }, [selectedOrg, router]);

    if (isLoading) {
        return <Loader />;
    }

    return (
        <div className="container mx-auto p-4">
            {/* Change to a proper readme or get started guide */}
            <Card className="max-w-md mx-auto">
                <CardHeader>
                    <CardTitle>Get Started</CardTitle>
                    <CardDescription>
                        Create your first organization to begin
                    </CardDescription>
                </CardHeader>
            </Card>
        </div>
    );
}
