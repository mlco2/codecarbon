"use client";

import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import Loader from "@/components/loader";
import { Organization } from "@/types/organization";
import { fetcher } from "@/helpers/swr";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR from "swr";

export default function HomePage() {
    const router = useRouter();
    const [redirecting, setRedirecting] = useState(true);
    
    // Fetch organizations to find the default
    const { data: organizations, error } = useSWR<Organization[]>('/organizations', fetcher, {
        revalidateOnFocus: false,
    });
    
    useEffect(() => {
        // Check if we have organizations data
        if (organizations && organizations.length > 0) {
            // Find default org ID - using the first organization
            const defaultOrgId = organizations[0].id;
            
            // Save to localStorage
            try {
                localStorage.setItem("organizationId", defaultOrgId);
                localStorage.setItem("organizationName", organizations[0].name || '');
            } catch (error) {
                console.error("Error writing to localStorage:", error);
            }
            
            // Navigate to the organization page without a page reload
            router.push(`/${defaultOrgId}`);
        } else if (organizations && organizations.length === 0 || error) {
            setRedirecting(false);
        }
    }, [organizations, router, error]);
    
    // Show a loader while we fetch the data and redirect
    if (redirecting) {
        return <Loader />;
    }
    
    // Fallback content if there are no organizations
    return (
        <div className="container mx-auto p-4">
            <Card className="mx-auto">
                <CardHeader>
                    <CardTitle>Get Started</CardTitle>
                    <CardDescription>
                        You can do that by installing the command line tool and
                        running:
                        <span className="block whitespace-pre-wrap border-l-2 border-[#3498db] break-words pl-4 m-4">
                            codecarbon login <br />
                            codecarbon config <br />
                            codecarbon monitor
                        </span>
                        You&apos;ll then need to get the project id from the
                        config file before generating the token.
                        <br />
                        You can then write the token in the config file and
                        start monitoring. <br />
                        <br />
                        For more information, please refer to the documentation:
                        <br />
                        <a
                            href="https://mlco2.github.io/codecarbon/usage.html"
                            target="_blank"
                        >
                            https://mlco2.github.io/codecarbon/usage.html
                        </a>
                    </CardDescription>
                </CardHeader>
            </Card>
        </div>
    );
}
