function trimTrailingSlash(value: string): string {
    return value.endsWith("/") ? value.slice(0, -1) : value;
}

/**
 * Build the OAuth login URL. Returns `null` when `VITE_API_URL` is not
 * configured (typically a local `pnpm dev` session with no `.env`),
 * so callers can render a disabled button instead of crashing the page.
 */
export function buildLoginUrl(): string | null {
    const apiBase = trimTrailingSlash(import.meta.env.VITE_API_URL ?? "");
    const appBase = trimTrailingSlash(import.meta.env.VITE_BASE_URL ?? "");
    if (!apiBase) {
        console.warn(
            "[auth] VITE_API_URL is not set — login is disabled. " +
                "Configure it in webapp/.env (see .env.example).",
        );
        return null;
    }
    const url = new URL(`${apiBase}/auth/login`);
    url.searchParams.set("redirect", `${appBase}/home?auth=true`);
    return url.toString();
}

/**
 * Navigate the browser to the OAuth login endpoint. No-op when the login
 * URL cannot be built (missing config) — the caller should display a
 * helpful message instead.
 */
export function redirectToLogin(): void {
    const url = buildLoginUrl();
    if (!url) return;
    window.location.assign(url);
}
