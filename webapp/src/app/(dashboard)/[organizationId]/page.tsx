"use client";

import { useEffect, useState } from "react";

import { DateRange } from "react-day-picker";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Separator } from "@/components/ui/separator";
import RadialChart from "@/components/radial-chart";
import { fetcher } from "@/helpers/swr";
import { Organization } from "@/types/organization";
import { OrganizationReport } from "@/types/organization-report";
import useSWR from "swr";
import { getOrganizationEmissionsByProject } from "@/server-functions/organizations";
import {
    getEquivalentHouseHoldPercentage,
    getEquivalentCarKm,
    getEquivalentTvTime,
} from "@/helpers/constants";

export default function OrganizationPage({
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
    const [organizationReport, setOrganizationReport] = useState<
        OrganizationReport | undefined
    >({ name: "", duration: 0, emissions: 0, energy_consumed: 0 });

    useEffect(() => {
        async function fetchOrganizationReport() {
            const organizationReport: OrganizationReport | null =
                await getOrganizationEmissionsByProject(
                    params.organizationId,
                    date,
                );
            if (organizationReport) {
                setOrganizationReport(organizationReport);
            }
        }

        fetchOrganizationReport();
    }, [params.organizationId, date]);
    if (isLoading) {
        return <Loader />;
    }

    if (error) {
        return <ErrorMessage />;
    }

    const RadialChartData = {
        energy: {
            label: "kWh",
            value: organizationReport?.energy_consumed
                ? parseFloat(organizationReport.energy_consumed.toFixed(2))
                : 0,
        },
        emissions: {
            label: "kg eq CO2",
            value: organizationReport?.emissions
                ? parseFloat(organizationReport.emissions.toFixed(2))
                : 0,
        },
        duration: {
            label: "days",
            value: organizationReport?.duration
                ? parseFloat(
                      (organizationReport.duration / 86400, 0).toFixed(2),
                  )
                : 0,
        },
    };

    const household_converted_value = getEquivalentHouseHoldPercentage(
        RadialChartData.emissions.value,
    ).toFixed(2);
    const transportation_converted_value = getEquivalentCarKm(
        RadialChartData.emissions.value,
    ).toFixed(2);
    const tv_time_converted_value = getEquivalentTvTime(
        RadialChartData.emissions.value,
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
