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
): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {}),
        },
    });

    if (!response.ok) {
        let errorMessage = `API error: ${response.status} ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
        } catch (e) {
            // Ignore JSON parsing errors
        }
        throw new Error(errorMessage);
    }

    return response.json();
}
