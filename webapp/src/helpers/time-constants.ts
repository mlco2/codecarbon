/**
 * Time-related constants to avoid magic numbers
 */

// Base time units in milliseconds
export const MILLISECONDS_PER_SECOND = 1000;
export const SECONDS_PER_MINUTE = 60;
export const MINUTES_PER_HOUR = 60;
export const HOURS_PER_DAY = 24;
export const DAYS_PER_WEEK = 7;
export const WEEKS_PER_YEAR = 52;

// Composite time units in milliseconds
export const ONE_SECOND_MS = MILLISECONDS_PER_SECOND;
export const ONE_MINUTE_MS = ONE_SECOND_MS * SECONDS_PER_MINUTE;
export const ONE_HOUR_MS = ONE_MINUTE_MS * MINUTES_PER_HOUR;
export const ONE_DAY_MS = ONE_HOUR_MS * HOURS_PER_DAY;
export const ONE_WEEK_MS = ONE_DAY_MS * DAYS_PER_WEEK;

// Common time intervals
export const THIRTY_DAYS_MS = 30 * ONE_DAY_MS;

// Seconds conversions
export const SECONDS_PER_HOUR = SECONDS_PER_MINUTE * MINUTES_PER_HOUR;
export const SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY;

// Common refresh intervals
export const REFRESH_INTERVAL_ONE_MINUTE = ONE_MINUTE_MS;
