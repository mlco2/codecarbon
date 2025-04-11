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
    try {
        // Check if we're in the browser
        if (typeof window !== "undefined") {
            return await fetchApiClient<T>(endpoint, options);
        } else {
            // Server-side - use fetchApiServer
            return await fetchApiServer<T>(endpoint, options);
        }
    } catch (error) {
        // Log and rethrow the error for other endpoints
        console.error(`API error for ${endpoint}:`, error);
        throw error;
    }
}

// Helper function to check if we're running on the client
export function isClient(): boolean {
    return typeof window !== "undefined";
}

// Helper function to check if we're running on the server
export function isServer(): boolean {
    return typeof window === "undefined";
}
