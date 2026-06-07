import { format } from "date-fns";

/**
 * Pick a date-fns format string that fits the span between two timestamps.
 * Use this for axis tick labels so a 30-second range doesn't print the date 10
 * times and a 6-month range doesn't print the minute.
 */
export function pickTimeFormat(spanMs: number): string {
    const minute = 60_000;
    const hour = 60 * minute;
    const day = 24 * hour;

    if (spanMs < 2 * minute) return "HH:mm:ss";
    if (spanMs < day) return "HH:mm";
    if (spanMs < 7 * day) return "MMM d, HH:mm";
    if (spanMs < 365 * day) return "MMM d";
    return "MMM yyyy";
}

export function formatTick(timestampMs: number, spanMs: number): string {
    return format(new Date(timestampMs), pickTimeFormat(spanMs));
}
