import { addMonths, startOfDay, endOfDay } from "date-fns";

/**
 * Returns a default date range for filtering data
 * @param months Number of months to go back from today (defaults to 2)
 * @returns DateRange object with from and to dates
 */
export const getDefaultDateRange = (
    months: number = 2,
): { from: Date; to: Date } => {
    const today = new Date();
    return {
        from: startOfDay(addMonths(today, -months)),
        to: endOfDay(today),
    };
};
