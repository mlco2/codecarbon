"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE_NAME } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

/**
 * Fetch API with authentication for server-side requests
 * Uses cookie-based auth for server components/actions
 */
export async function fetchApiServer<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T | null> {
    try {
        // Get session cookie for server-side auth
        const cookieStore = await cookies();
        const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

        if (!sessionCookie?.value) {
            redirect(
                `${process.env.NEXT_PUBLIC_API_URL}/auth/login?redirect=${process.env.NEXT_PUBLIC_BASE_URL}/home?auth=true`,
            );
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                Cookie: `${SESSION_COOKIE_NAME}=${sessionCookie.value}`,
                ...(options?.headers || {}),
            },
        });

        if (!response.ok) {

            if ((response.status === 401)) {
                redirect(
                    `${process.env.NEXT_PUBLIC_API_URL}/auth/login?redirect=${process.env.NEXT_PUBLIC_BASE_URL}/home?auth=true`,
                );
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

        // Parse JSON response
        try {
            return await response.json();
        } catch (e) {
            // If JSON parsing fails (e.g., empty response body), return null
            console.warn(
                `Empty or invalid JSON response from ${endpoint}, returning null`,
            );
            return null;
        }
    } catch (error) {

        if(
            error instanceof Error &&
            (error.message == "NEXT_REDIRECT" ||
                (error as any).digest?.startsWith("NEXT_REDIRECT"))
        ) {
            throw error;
        }

        // Log server-side error with more details
        console.error("API server request failed:", {
            endpoint,
            error: error instanceof Error ? error.message : String(error),
        });

        // Return null to let callers handle defaults appropriately
        return null;
    }
}
