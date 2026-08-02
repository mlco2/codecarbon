import { ZodSchema } from "zod";
import { fetchApi } from "./client";
import { handleError } from "./errors";

const API_BASE = import.meta.env.VITE_API_URL;

export const fetcher = async (url: string) => {
  const res = await fetch(`${API_BASE}${url}`, { credentials: "include" });
  if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
  return res.json();
};

export function createValidatedFetcher<T>(schema: ZodSchema<T>) {
  return (url: string) => fetchApi(url, schema);
}

export const swrConfig = {
  onError: handleError,
  dedupingInterval: 5000,
  focusThrottleInterval: 30000,
  revalidateOnFocus: false,
};
