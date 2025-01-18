// "use server";
import { IProjectToken } from "@/types/project";

/**
 * Retrieves the list of tokens for a given project
 */
export async function getProjectTokens(
    projectId: string,
): Promise<IProjectToken[]> {
    try {
        const URL = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/api-tokens`;
        const res = await fetch(URL, {
            credentials: "include",
        });

        console.log("Response status:", res.status);
        console.log("Response headers:", res.headers);
        if (!res.ok) {
            // This will activate the closest `error.js` Error Boundary
            console.error("Failed to fetch data", res.statusText);
            throw new Error("Failed to fetch data");
        }
        const data = await res.json();
        return data;
    } catch (error) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }
}

export async function createProjectToken(
    projectId: string,
    tokenName: string,
    access?: Number,
): Promise<IProjectToken> {
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/api-tokens`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ name: tokenName, access }),
                credentials: "include",
            },
        );
        if (!res.ok) {
            // This will activate the closest `error.js` Error Boundary
            console.error("Failed to fetch data", res.statusText);
            throw new Error("Failed to fetch data");
        }
        return res.json();
    } catch (error) {
        // This will activate the closest `error.js` Error Boundary
        console.error("Failed to fetch data", error);
        throw new Error("Failed to fetch data");
    }
}
export async function deleteProjectToken(
    projectId: string,
    tokenId: string,
): Promise<void> {
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/api-tokens/${tokenId}`,
            {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
            },
        );
        if (res.status !== 204) {
            // This will activate the closest `error.js` Error Boundary
            console.error("Failed to fetch data", res.statusText);
            throw new Error("Failed to fetch data");
        }
        return;
    } catch (error) {
        // This will activate the closest `error.js` Error Boundary
        console.error("Failed to fetch data", error);
        throw new Error("Failed to fetch data");
    }
}
