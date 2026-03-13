import { fetchApiClient } from "@/helpers/api-client";
import { fetchApiServer } from "@/helpers/api-server";

/**
 * API utility functions that help determine whether to use client or server API
 * and provide consistent error handling
 */

// Universal API function that works in both client and server components
export async function fetchApi<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T | null> {
    // Both fetchApiClient and fetchApiServer handle errors internally
    // and return null on failure, so no try/catch needed here
    if (typeof window !== "undefined") {
        return await fetchApiClient<T>(endpoint, options);
    }
    return await fetchApiServer<T>(endpoint, options);
}
