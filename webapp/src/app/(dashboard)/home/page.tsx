// "use client";

import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { fiefAuth } from "@/helpers/fief";
import { getDefaultOrgId } from "@/server-functions/organizations";
import { redirect } from "next/navigation";

// This method calls the API to check if the user is created in DB
async function checkAuth() {
    const token = fiefAuth.getAccessTokenInfo();
    if (!token) {
        throw new Error("No token found");
    }
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        headers: {
            Authorization: `Bearer ${token?.access_token}`,
        },
    });

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch /auth/login");
    }

    return res.json();
}

export default async function HomePage({
    params,
    searchParams,
}: {
    params: { slug: string };
    searchParams: { [key: string]: string | string[] | undefined };
}) {
    if (searchParams && searchParams["auth"]) {
        try {
            const res = await checkAuth();
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
            <Card className="max-w-md mx-auto">
                <CardHeader>
                    <CardTitle>Get Started</CardTitle>
                    <CardDescription>
                        You can do that by installing the command line tool and
                        running:
                        <span
                            style={{
                                display: "block",
                                whiteSpace: "pre-wrap",
                                borderLeft: "2px solid #3498db",
                                wordWrap: "break-word",
                                paddingLeft: "1em",
                                margin: "1em",
                            }}
                        >
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
