function trimTrailingSlash(value: string): string {
    return value.endsWith("/") ? value.slice(0, -1) : value;
}

/**
 * Build a URL on the auth endpoints. Returns `null` when `VITE_API_URL` is
 * not configured (typically a local `pnpm dev` session with no `.env`),
 * so callers can render a disabled control instead of crashing the page.
 */
function buildAuthUrl(path: string, action: string): string | null {
    const apiBase = trimTrailingSlash(import.meta.env.VITE_API_URL ?? "");
    if (!apiBase) {
        console.warn(
            `[auth] VITE_API_URL is not set — ${action} is disabled. ` +
                "Configure it in webapp/.env (see .env.example).",
        );
        return null;
    }
    return new URL(`${apiBase}${path}`).toString();
}

/** Build the OAuth login URL, or `null` when the API is not configured. */
export function buildLoginUrl(): string | null {
    return buildAuthUrl("/auth/login", "login");
}

/** Build the logout URL, or `null` when the API is not configured. */
export function buildLogoutUrl(): string | null {
    return buildAuthUrl("/auth/logout", "logout");
}

/**
 * Build the URL that sends the user to the identity provider's account
 * console, or `null` when the API is not configured. The API owns the
 * issuer URL and redirects, the same way it does for login.
 */
export function buildAccountUrl(): string | null {
    return buildAuthUrl("/auth/account", "the account link");
}

function redirectTo(url: string | null): void {
    if (!url) return;
    window.location.assign(url);
}

/**
 * Navigate the browser to the OAuth login endpoint. No-op when the login
 * URL cannot be built (missing config) — the caller should display a
 * helpful message instead.
 */
export function redirectToLogin(): void {
    redirectTo(buildLoginUrl());
}

/** Navigate the browser to the logout endpoint. No-op without API config. */
export function redirectToLogout(): void {
    redirectTo(buildLogoutUrl());
}

/** Navigate the browser to the account console. No-op without API config. */
export function redirectToAccount(): void {
    redirectTo(buildAccountUrl());
}
