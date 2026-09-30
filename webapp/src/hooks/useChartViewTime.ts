import { useEffect, useRef } from "react";
import { trackEvent } from "@/utils/matomo";

// Views shorter than this are scrolling past, not reading.
const MIN_VIEW_SECONDS = 2;

/*
 * Reports how long a section stayed at least half on screen, in one event
 * sent when the section goes away, so a chart that is looked at for a minute
 * costs one request rather than a heartbeat. Time only counts while the tab
 * is visible.
 */
export function useChartViewTime<T extends Element>(name: string) {
    const ref = useRef<T>(null);

    useEffect(() => {
        const element = ref.current;
        if (!element || typeof IntersectionObserver === "undefined") return;

        let total = 0;
        let since: number | null = null;
        let inView = false;

        const stop = () => {
            if (since !== null) total += performance.now() - since;
            since = null;
        };
        const sync = () => {
            if (inView && document.visibilityState === "visible") {
                since ??= performance.now();
            } else {
                stop();
            }
        };
        const flush = () => {
            stop();
            const seconds = Math.round(total / 1000);
            total = 0;
            if (seconds >= MIN_VIEW_SECONDS) {
                trackEvent("Dashboard", "chart_viewed", name, seconds);
            }
        };

        const observer = new IntersectionObserver(
            ([entry]) => {
                inView = entry.isIntersecting;
                sync();
            },
            { threshold: 0.5 },
        );
        observer.observe(element);
        document.addEventListener("visibilitychange", sync);
        window.addEventListener("pagehide", flush);

        return () => {
            observer.disconnect();
            document.removeEventListener("visibilitychange", sync);
            window.removeEventListener("pagehide", flush);
            flush();
        };
    }, [name]);

    return ref;
}
