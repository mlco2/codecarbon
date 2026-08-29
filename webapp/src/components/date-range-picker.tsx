import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/helpers/utils";
import { CalendarIcon } from "lucide-react";
import { useState } from "react";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";

interface DateRangePickerProps {
    date: DateRange;
    onDateChange: (newDate: DateRange | undefined) => void;
    /**
     * `default` keeps the outline button used elsewhere in the app.
     * `dashboard` matches the design's "Input" component: a 16px
     * IBM Plex Mono Regular "Dates" label above a 46px field with a
     * rgba(255,255,255,0.05) fill, 2px radius, 16px horizontal padding and a
     * #666666 numeric value. The design shows no calendar glyph in the field.
     */
    variant?: "default" | "dashboard";
    /** Field label, used by the `dashboard` variant. */
    label?: string;
}

export function DateRangePicker({
    date,
    onDateChange,
    variant = "default",
    label = "Dates",
}: DateRangePickerProps) {
    const [open, setOpen] = useState(false);
    const [tempDateRange, setTempDateRange] = useState<DateRange | undefined>(
        date,
    );

    const handleOpenChange = (newOpen: boolean) => {
        setOpen(newOpen);
        if (newOpen) {
            // Sync tempDateRange with current date when opening
            setTempDateRange(date);
        }
    };

    const handleApply = () => {
        onDateChange(tempDateRange);
        setOpen(false);
    };

    /*
     * The design renders the range as "01/01/2021 - 01/02/2021". A one-month
     * span is dd/MM/yyyy (1 Jan to 1 Feb), which also matches this dashboard's
     * default 30-day range; read as MM/dd/yyyy it would be a single day.
     */
    const formatted = (pattern: string) =>
        date?.from
            ? date.to
                ? `${format(date.from, pattern)} - ${format(date.to, pattern)}`
                : format(date.from, pattern)
            : null;

    const trigger =
        variant === "dashboard" ? (
            <div className="flex w-full flex-col gap-1">
                <label
                    htmlFor="date"
                    className="type-mono-regular type-field text-cc-white"
                >
                    {label}
                </label>
                <PopoverTrigger asChild>
                    <button
                        id="date"
                        type="button"
                        className="flex h-control w-full items-center rounded-field bg-white/5 px-4 text-left outline-none focus-visible:ring-2 focus-visible:ring-cc-lime"
                    >
                        <span className="type-mono-regular type-field truncate text-cc-text-input-gray">
                            {formatted("dd/MM/yyyy") ?? "Pick a date"}
                        </span>
                    </button>
                </PopoverTrigger>
            </div>
        ) : (
            <PopoverTrigger asChild>
                <Button
                    id="date"
                    variant={"outline"}
                    className={cn(
                        "w-[300px] justify-start text-left font-normal",
                        !date && "text-muted-foreground",
                    )}
                >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {formatted("LLL dd, y") ?? <span>Pick a date</span>}
                </Button>
            </PopoverTrigger>
        );

    return (
        <Popover open={open} onOpenChange={handleOpenChange}>
            {trigger}
            <PopoverContent className="w-auto p-0" align="start">
                <div className="p-0">
                    <Calendar
                        initialFocus
                        mode="range"
                        defaultMonth={date?.from}
                        selected={tempDateRange}
                        onSelect={(range) => {
                            setTempDateRange(range);
                        }}
                        numberOfMonths={2}
                    />
                    <div className="flex items-center justify-end gap-2 p-3 border-t">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                setTempDateRange(date);
                                setOpen(false);
                            }}
                        >
                            Cancel
                        </Button>
                        <Button
                            size="sm"
                            onClick={handleApply}
                            disabled={
                                !tempDateRange?.from || !tempDateRange?.to
                            }
                        >
                            Apply
                        </Button>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    );
}
