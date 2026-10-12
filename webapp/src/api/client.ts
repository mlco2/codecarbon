import { z, ZodTypeAny } from "zod";
import { ApiError, ValidationError } from "./errors";

const API_BASE = import.meta.env.VITE_API_URL;

async function throwApiError(
    response: Response,
    endpoint: string,
): Promise<never> {
    let detail = `${response.status} ${response.statusText}`;
    try {
        const body = await response.json();
        detail = body.detail || detail;
    } catch {
        // Keep the HTTP status text when the response is not JSON.
    }
    throw new ApiError(detail, response.status, endpoint);
}

// Accept any zod schema, including ones produced by `.transform(...)` whose
// input and output types differ. The function's return type is the schema's
// *output* type.
export async function fetchApi<S extends ZodTypeAny>(
    endpoint: string,
    schema: S,
    options?: RequestInit,
): Promise<z.infer<S>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {}),
        },
    });

    if (!response.ok) {
        return throwApiError(response, endpoint);
    }

    if (response.status === 204) return undefined as z.infer<S>;

    const data = await response.json();
    const parsed = schema.safeParse(data);
    if (!parsed.success) {
        throw new ValidationError(
            `Invalid response from ${endpoint}`,
            parsed.error,
            endpoint,
        );
    }
    return parsed.data;
}

export async function fetchApiVoid(
    endpoint: string,
    options?: RequestInit,
): Promise<void> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {}),
        },
    });

    if (!response.ok) {
        await throwApiError(response, endpoint);
    }
}

export async function fetchApiJson<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        credentials: "include",
    });
    if (!response.ok) {
        return throwApiError(response, endpoint);
    }
    return response.json() as Promise<T>;
}
