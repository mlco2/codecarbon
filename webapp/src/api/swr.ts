import { fetchApiJson } from "./client";
import { handleError } from "./errors";

export const fetcher = <T>(endpoint: string) => fetchApiJson<T>(endpoint);

export const swrConfig = {
    onError: handleError,
    dedupingInterval: 5000,
    focusThrottleInterval: 30000,
    revalidateOnFocus: false,
};
