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
        ? new URL(apiBase).pathname.replace(/\/$/, "")
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

        const isApiCall = apiBase ? rawUrl.startsWith(apiBase) : false;

        if (!isApiCall) return realFetch(input, init);

        const url = new URL(rawUrl);
        const relPath =
            apiPathPrefix && url.pathname.startsWith(apiPathPrefix)
                ? url.pathname.slice(apiPathPrefix.length) || "/"
                : url.pathname;
        const relUrl = new URL(relPath + url.search, "http://mock.local");
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
