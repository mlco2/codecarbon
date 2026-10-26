// Matomo page-view tracking for the webapp.
//
// The webapp is a single-page app, so Matomo's stock snippet would only see
// the first load. We send the first page view ourselves, then one per
// pathname change by listening to the router. Query strings are left out of
// the tracked URL on purpose: they carry filter state, not distinct pages.
//
// Tracking stays off unless both env vars are set, so local dev and the mock
// build never pollute the production site.

type MatomoCommand = (string | number)[];

interface TrackedRouter {
    state: { location: { pathname: string } };
    subscribe(
        listener: (state: { location: { pathname: string } }) => void,
    ): () => void;
}

declare global {
    interface Window {
        _paq?: MatomoCommand[];
    }
}

let enabled = false;

function push(command: MatomoCommand) {
    (window._paq = window._paq || []).push(command);
}

function trackPageView(pathname: string) {
    push(["setCustomUrl", window.location.origin + pathname]);
    push(["trackPageView"]);
}

/**
 * Record a custom event. A no-op until `initMatomo` has enabled tracking, so
 * call sites never need to check the environment. Pass only categories and
 * counts: nothing that identifies a person.
 */
export function trackEvent(
    category: string,
    action: string,
    name?: string,
    value?: number,
): void {
    if (!enabled) return;
    const command: MatomoCommand = ["trackEvent", category, action];
    if (name !== undefined || value !== undefined) command.push(name ?? "");
    if (value !== undefined) command.push(value);
    push(command);
}

export function initMatomo(router: TrackedRouter): void {
    const baseUrl = import.meta.env.VITE_MATOMO_URL;
    const siteId = import.meta.env.VITE_MATOMO_SITE_ID;
    if (!baseUrl || !siteId) return;
    enabled = true;

    const url = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
    // Cookieless, so the dashboard needs no consent banner for analytics.
    push(["disableCookies"]);
    push(["enableLinkTracking"]);
    push(["setTrackerUrl", `${url}matomo.php`]);
    push(["setSiteId", siteId]);

    const script = document.createElement("script");
    script.async = true;
    script.src = `${url}matomo.js`;
    document.head.appendChild(script);

    let lastPathname = router.state.location.pathname;
    trackPageView(lastPathname);

    router.subscribe((state) => {
        const { pathname } = state.location;
        if (pathname === lastPathname) return;
        lastPathname = pathname;
        trackPageView(pathname);
    });
}
