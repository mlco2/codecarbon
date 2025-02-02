// "use client";

import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { getDefaultOrgId } from "@/server-functions/organizations";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

// This method calls the API to check if the user is created in DB
async function checkAuth() {
    const headersList = await headers();
    const token = headersList.get("X-FiefAuth-Access-Token-Info");

    if (!token) {
        throw new Error("No token found");
    }
    const tokenInfo = JSON.parse(token);
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        headers: {
            Authorization: `Bearer ${tokenInfo.access_token}`,
        },
    });

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch /auth/login");
    }
}

export default async function HomePage({
    searchParams,
}: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const { auth } = await searchParams;

    if (auth) {
        try {
            await checkAuth();
        } catch (error) {
            console.error("Error with /check/auth:", error);
        }
    }

    const orgId = await getDefaultOrgId();
    if (orgId) {
        redirect(`/${orgId}`);
    }

    return (
        <div className="container mx-auto p-4">
            {/* Change to a proper readme or get started guide */}
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
