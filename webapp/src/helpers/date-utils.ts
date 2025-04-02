import { addMonths, startOfDay, endOfDay } from "date-fns";

export const getDefaultDateRange = (): { from: Date; to: Date } => {
    const today = new Date();
    return {
        from: startOfDay(addMonths(today, -2)),
        to: endOfDay(today),
    };
};
