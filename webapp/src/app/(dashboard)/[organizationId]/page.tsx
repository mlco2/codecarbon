"use client";

import { CalendarIcon } from "lucide-react";
import { useState } from "react";

import { cn } from "@/helpers/utils";

import { DateRange } from "react-day-picker";
import { format } from "date-fns";

import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";

import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import RadialChart from "@/components/radial-chart";
import { fetcher } from "@/helpers/swr";
import { Organization } from "@/types/organization";
import { OrganizationReport } from "@/types/organization-report";
import useSWR from "swr";

async function getOrganizationEmissionsByProject(
    organizationId: string,
    dateRange: DateRange | undefined,
): Promise<OrganizationReport> {
    let url = `${process.env.NEXT_PUBLIC_API_URL}/organizations/${organizationId}/sums`;

    if (dateRange) {
        url += `?start_date=${dateRange.from?.toISOString()}&end_date=${dateRange.to?.toISOString()}`;
    }

    const res = await fetch(url);
    const result = await res.json();
    return {
        name: result.name,
        emissions: result.emissions * 1000,
        energy_consumed: result.energy_consumed * 1000,
        duration: result.duration,
    };
}

export default async function OrganizationPage({
    params,
}: {
    params: { organizationId: string };
}) {
    const {
        data: organization,
        isLoading,
        error,
    } = useSWR<Organization>(
        `/organizations/${params.organizationId}`,
        fetcher,
        {
            refreshInterval: 1000 * 60, // Refresh every minute
        },
    );

    const today = new Date();
    const [date, setDate] = useState<DateRange | undefined>({
        from: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000),
        to: today,
    });

    if (isLoading) {
        return <Loader />;
    }

    if (error) {
        return <ErrorMessage />;
    }
    const organizationReport = await getOrganizationEmissionsByProject(
        params.organizationId,
        date,
    );
    const RadialChartData = {
        energy: {
            label: "kWh",
            value: organizationReport
                ? parseFloat(organizationReport.energy_consumed.toFixed(2))
                : 0,
        },
        emissions: {
            label: "kg eq CO2",
            value: organizationReport
                ? parseFloat(organizationReport.emissions.toFixed(2))
                : 0,
        },
        duration: {
            label: "days",
            value: organizationReport
                ? parseFloat(
                      (organizationReport.duration / 86400, 0).toFixed(2),
                  )
                : 0,
        },
    };

    const household_converted_value = (
        (RadialChartData.emissions.value * 100) /
        160.58
    ).toFixed(2);
    const transportation_converted_value = (
        RadialChartData.emissions.value / 0.409
    ).toFixed(2);
    const tv_time_converted_value = (
        RadialChartData.emissions.value /
        (0.097 * 24)
    ).toFixed(2);

    return (
        <div className="h-full w-full overflow-auto">
            {!organization && <ErrorMessage />}
            {organization && (
                <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                    <Separator className="h-[0.5px] bg-muted-foreground" />
                    <div className="grid grid-cols-3 gap-4">
                        <div className="flex flex-col items-center justify-center">
                            <img
                                src="/household_consumption.svg"
                                alt="Logo 1"
                                className="h-16 w-16"
                            />
                            <p className="text-xs text-gray-500">
                                {household_converted_value} %
                            </p>
                            <p className="text-sm font-medium">
                                Of an american household weekly energy
                                consumption
                            </p>
                        </div>
                        <div className="flex flex-col items-center justify-center">
                            <img
                                src="/transportation.svg"
                                alt="Logo 2"
                                className="h-16 w-16"
                            />
                            <p className="text-xs text-gray-500">
                                {transportation_converted_value}
                            </p>
                            <p className="text-sm font-medium">
                                Kilometers ridden
                            </p>
                        </div>
                        <div className="flex flex-col items-center justify-center">
                            <img
                                src="/tv.svg"
                                alt="Logo 3"
                                className="h-16 w-16"
                            />
                            <p className="text-xs text-gray-500">
                                {tv_time_converted_value} days
                            </p>
                            <p className="text-sm font-medium">
                                Of watching TV
                            </p>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                        <RadialChart data={RadialChartData.energy} />
                        <RadialChart data={RadialChartData.emissions} />
                        <RadialChart data={RadialChartData.duration} />
                    </div>
                </main>
            )}
        </div>
    );
}
