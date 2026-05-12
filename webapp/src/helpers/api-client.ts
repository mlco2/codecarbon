"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

/**
 * Client-side API wrapper with authentication
 * Accepts access token as parameter instead of retrieving it directly
 *
 * Usage example:
 * ```
 * 'use client'
 * import { fetchApiClient, getAccessToken } from "@/helpers/api-client";
 *
 * // In your component:
 * const accessToken = getAccessToken();
 * const data = await fetchApiClient("/projects", {}, accessToken);
 * ```
 */
export async function fetchApiClient<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T | null> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {}),
        },
    });

    if (!response.ok) {
        if (response.status == 401) {
            window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/login?redirect=${process.env.NEXT_PUBLIC_BASE_URL}/home?auth=true`;
            return null;
        }
        let errorMessage = `API error: ${response.status} ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
        } catch (e) {
            // Ignore JSON parsing errors
        }
        console.error(errorMessage);
        return null;
    }

    // Handle 204 No Content responses (e.g., DELETE operations)
    if (response.status === 204) {
        return null;
    }

    return response.json();
}
