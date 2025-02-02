import { fiefAuth } from "@/helpers/fief";
import { headers } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export async function fetchApi<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T | null> {
    const headersList = await headers();
    const token = headersList.get("X-FiefAuth-Access-Token-Info");
    if (!token) {
        console.log("No token found");
        return null;
    }

    const tokenInfo = JSON.parse(token);
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            Authorization: `Bearer ${tokenInfo.access_token}`,
        },
    });

    if (!response.ok) {
        console.log(`API call failed: ${response.statusText}`);
        return null;
    }

    return response.json();
}
