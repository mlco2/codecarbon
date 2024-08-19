import ErrorMessage from "@/components/error-message";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { fiefAuth } from "@/helpers/fief";
import { redirect } from "next/navigation";

// This method calls the API to check if the user is created in DB
async function checkAuth() {
    const token = fiefAuth.getAccessTokenInfo();
    if (!token) {
        console.log("No token found")
        throw new Error("No token found");
    }
    console.log("checkAuth() 20")
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        headers: {
            Authorization: `Bearer ${token?.access_token}`,
        },
    });

    console.log("checkAuth() 300")
    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch /auth/login");
    }

    return res.json();
}

async function getDefaultOrgId(): Promise<string | null> {
    console.log("Being invoked")
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/organizations`);

    if (!res.ok) {
        throw new Error("Failed to fetch /organizations");
    }

    const orgs = await res.json();
    console.log(orgs)
    if (orgs.length > 0) {
        return orgs[0].id;
    }
    return null;
}

export default async function HomePage({
    params,
    searchParams,
}: {
    params: { slug: string };
    searchParams: { [key: string]: string | string[] | undefined };
}) {
    console.log("HomePage params:", searchParams);
    if (searchParams && searchParams["auth"]) {
        try {
            const res = await checkAuth();
            console.log("User is authenticated:", res);
        } catch (error) {
            console.error("Error with /auth/check:", error);
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
                        Create your first organization to begin
                    </CardDescription>
                </CardHeader>
            </Card>
        </div>
    );
}
