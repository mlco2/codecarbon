"use server";

import { cookies } from "next/headers";
import { SESSION_COOKIE_NAME } from "./fief";

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
            throw new Error("No authentication session found");
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
            let errorMessage = `API error: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Ignore JSON parsing errors
            }
            console.log(errorMessage);
            return null;
        }

        // Handle 204 No Content responses (e.g., DELETE operations)
        if (response.status === 204) {
            return null;
        }

        // Special handling for endpoints that might return null
        if (
            endpoint.includes("/organizations/") &&
            endpoint.includes("/sums")
        ) {
            // For organization sums endpoint that might return null
            try {
                return await response.json();
            } catch (e) {
                // If JSON parsing fails (e.g., empty response), return default values
                console.warn(
                    "Empty response from organization sums endpoint, using default values",
                );
                return {
                    name: "",
                    description: "",
                    emissions: 0,
                    energy_consumed: 0,
                    duration: 0,
                    cpu_power: 0,
                    gpu_power: 0,
                    ram_power: 0,
                    emissions_rate: 0,
                    emissions_count: 0,
                } as unknown as T;
            }
        }

        return await response.json();
    } catch (error) {
        // Log server-side error with more details
        console.error("API server request failed:", {
            endpoint,
            error: error instanceof Error ? error.message : String(error),
        });

        // For organization sums endpoint, return default values instead of throwing
        if (
            endpoint.includes("/organizations/") &&
            endpoint.includes("/sums")
        ) {
            return {
                name: "",
                description: "",
                emissions: 0,
                energy_consumed: 0,
                duration: 0,
                cpu_power: 0,
                gpu_power: 0,
                ram_power: 0,
                emissions_rate: 0,
                emissions_count: 0,
            } as unknown as T;
        }

        throw new Error("API request failed. Please try again.");
    }
}
