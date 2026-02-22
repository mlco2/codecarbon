import { resolveMock } from "./handlers";

export function isMockMode(): boolean {
    const flag = import.meta.env.VITE_USE_MOCK_DATA;
    return flag === "true" || flag === "1";
}

let installed = false;

export function installMockFetch(): void {
    if (installed || typeof window === "undefined") return;
    if (!isMockMode()) return;
    installed = true;

    const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
    const apiPathPrefix = apiBase
        ? (safeUrl(apiBase)?.pathname.replace(/\/$/, "") ?? "")
        : "";
    const realFetch = window.fetch.bind(window);

    window.fetch = async (
        input: RequestInfo | URL,
        init?: RequestInit,
    ): Promise<Response> => {
        const rawUrl =
            typeof input === "string"
                ? input
                : input instanceof URL
                  ? input.toString()
                  : input.url;

        // With an explicit VITE_API_URL we only intercept requests aimed at
        // it. With no VITE_API_URL (the default dev/mock setup), every
        // same-origin fetch is treated as an API call — Vite's static
        // assets are loaded via <script>/<link>/<img>, not fetch(), so
        // this interception is safe.
        const absoluteUrl = new URL(rawUrl, window.location.origin);
        const isApiCall = apiBase
            ? rawUrl.startsWith(apiBase)
            : absoluteUrl.origin === window.location.origin;

        if (!isApiCall) return realFetch(input, init);

        const relPath =
            apiPathPrefix && absoluteUrl.pathname.startsWith(apiPathPrefix)
                ? absoluteUrl.pathname.slice(apiPathPrefix.length) || "/"
                : absoluteUrl.pathname;
        const relUrl = new URL(
            relPath + absoluteUrl.search,
            "http://mock.local",
        );
        const method = (init?.method ?? "GET").toUpperCase();
        const parsedBody = parseBody(init?.body);
        const result = resolveMock(relUrl, method, parsedBody);

        await wait();

        if (result.status === 204) {
            return new Response(null, { status: 204 });
        }
        const body = JSON.stringify(result.body ?? {});
        return new Response(body, {
            status: result.status,
            headers: { "Content-Type": "application/json" },
        });
    };

    // eslint-disable-next-line no-console
    console.info(
        "[mock] fetch interceptor installed (VITE_USE_MOCK_DATA=true)",
    );
}

function safeUrl(value: string): URL | null {
    try {
        return new URL(value);
    } catch {
        return null;
    }
}

function parseBody(body: BodyInit | null | undefined): unknown {
    if (typeof body !== "string") return undefined;
    try {
        return JSON.parse(body);
    } catch {
        return body;
    }
}

function wait(ms = 50): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export function loginMock(): void {
    if (typeof window === "undefined") return;
    const baseUrl = (import.meta.env.VITE_BASE_URL ?? "").replace(/\/$/, "");
    window.location.assign(`${baseUrl}/home?auth=true`);
}
