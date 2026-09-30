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

function push(command: MatomoCommand) {
    (window._paq = window._paq || []).push(command);
}

function trackPageView(pathname: string) {
    push(["setCustomUrl", window.location.origin + pathname]);
    push(["trackPageView"]);
}

export function initMatomo(router: TrackedRouter): void {
    const baseUrl = import.meta.env.VITE_MATOMO_URL;
    const siteId = import.meta.env.VITE_MATOMO_SITE_ID;
    if (!baseUrl || !siteId) return;

    const url = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
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
