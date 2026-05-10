import { z, ZodTypeAny } from "zod";
import { ApiError, ValidationError } from "./errors";

const API_BASE = import.meta.env.VITE_API_URL;

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
        let detail = `${response.status} ${response.statusText}`;
        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch {
            // ignore JSON parse errors
        }
        throw new ApiError(detail, response.status, endpoint);
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
        let detail = `${response.status} ${response.statusText}`;
        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch {
            // ignore JSON parse errors
        }
        throw new ApiError(detail, response.status, endpoint);
    }
}
