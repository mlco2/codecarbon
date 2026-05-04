function trimTrailingSlash(value: string): string {
    return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function buildLoginUrl(): string {
    const apiBase = trimTrailingSlash(import.meta.env.VITE_API_URL ?? "");
    const appBase = trimTrailingSlash(import.meta.env.VITE_BASE_URL ?? "");
    const url = new URL(`${apiBase}/auth/login`);
    url.searchParams.set("redirect", `${appBase}/home?auth=true`);
    return url.toString();
}

export function redirectToLogin(): void {
    window.location.assign(buildLoginUrl());
}
