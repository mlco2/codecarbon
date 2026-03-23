import { ZodSchema } from "zod";
import { ApiError, ValidationError } from "./errors";

const API_BASE = import.meta.env.VITE_API_URL;

export async function fetchApi<T>(
  endpoint: string,
  schema: ZodSchema<T>,
  options?: RequestInit,
): Promise<T> {
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

  if (response.status === 204) return undefined as T;

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
