/**
 * Time-related constants to avoid magic numbers
 */

// Base time units
const SECONDS_PER_MINUTE = 60;
const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 24;

// Millisecond durations
const ONE_MINUTE_MS = 1000 * SECONDS_PER_MINUTE;
const ONE_DAY_MS = ONE_MINUTE_MS * MINUTES_PER_HOUR * HOURS_PER_DAY;

// Exported constants used across the app
export const THIRTY_DAYS_MS = 30 * ONE_DAY_MS;
export const SECONDS_PER_DAY =
    SECONDS_PER_MINUTE * MINUTES_PER_HOUR * HOURS_PER_DAY;
export const REFRESH_INTERVAL_ONE_MINUTE = ONE_MINUTE_MS;
