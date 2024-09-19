"use client";

import useSWR from "swr";
import { cn } from "@/helpers/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Activity, CreditCard, Users } from "lucide-react";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import RadialChart from "@/components/radial-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Project } from "@/types/project";
import { ExperimentReport } from "@/types/experiment-report";
import { fetcher } from "../../../../../helpers/swr";
import Loader from "@/components/loader";
import ErrorMessage from "@/components/error-message";
import { Calendar } from "@/components/ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DateRange } from "react-day-picker";

async function getProjectEmissionsByExperiment(
    projectId: string,
    dateRange: DateRange | undefined,
): Promise<ExperimentReport[]> {
    let url = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/experiments/sums/`;

    if (dateRange) {
        url += `?start_date=${dateRange.from?.toISOString()}&end_date=${dateRange.to?.toISOString()}`;
    }

    const res = await fetch(url);
    const result = await res.json();
    return result.map((experimentReport: ExperimentReport) => {
        return {
            experiment_id: experimentReport.experiment_id,
            name: experimentReport.name,
            emissions: experimentReport.emissions * 1000,
            energy_consumed: experimentReport.energy_consumed * 1000,
            duration: experimentReport.duration,
        };
    });
}

export default async function ProjectPage({
    params,
}: Readonly<{
    params: {
        projectId: string;
        className: string;
    };
}>) {
    const {
        data: project,
        isLoading,
        error,
    } = useSWR<Project>(`/projects/${params.projectId}`, fetcher, {
        refreshInterval: 1000 * 60, // Refresh every minute
    });

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

    if (project) {
        const experimentReport = await getProjectEmissionsByExperiment(
            project.id,
            date,
        );

        const RadialChartData = {
            energy: {
                label: "kWh",
                value: experimentReport
                    ? parseFloat(
                          experimentReport
                              .reduce(
                                  (n, { energy_consumed }) =>
                                      n + energy_consumed,
                                  0,
                              )
                              .toFixed(2),
                      )
                    : 0,
            },
            emissions: {
                label: "kg eq CO2",
                value: experimentReport
                    ? parseFloat(
                          experimentReport
                              .reduce((n, { emissions }) => n + emissions, 0)
                              .toFixed(2),
                      )
                    : 0,
            },
            duration: {
                label: "days",
                value: experimentReport
                    ? parseFloat(
                          experimentReport
                              .reduce(
                                  (n, { duration }) => n + duration / 86400,
                                  0,
                              )
                              .toFixed(2),
                      )
                    : 0,
            },
        };
        const ExperimentsData = {
            projectId: project.id,
            startDate: date?.from?.toISOString() ?? "",
            endDate: date?.to?.toISOString() ?? "",
        };
        const RunData = {
            experimentId: project.experiments[1],
            startDate: date?.from?.toISOString() ?? "",
            endDate: date?.to?.toISOString() ?? "",
        };
        return (
            <div className="h-full w-full overflow-auto">
                <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                    <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                        <div>
                            <h1 className="text-2xl font-semi-bold">
                                {project.name}
                            </h1>
                            <span className="text-sm font-semi-bold">
                                {project.description}
                            </span>
                        </div>
                        <div className={params.className}>
                            <Popover>
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
                                        {date?.from ? (
                                            date.to ? (
                                                <>
                                                    {format(
                                                        date.from,
                                                        "LLL dd, y",
                                                    )}{" "}
                                                    -{" "}
                                                    {format(
                                                        date.to,
                                                        "LLL dd, y",
                                                    )}
                                                </>
                                            ) : (
                                                format(date.from, "LLL dd, y")
                                            )
                                        ) : (
                                            <span>Pick a date</span>
                                        )}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent
                                    className="w-auto p-0"
                                    align="start"
                                >
                                    <Calendar
                                        initialFocus
                                        mode="range"
                                        defaultMonth={date?.from}
                                        selected={date}
                                        onSelect={setDate}
                                        numberOfMonths={2}
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                    </div>
                    <Separator className="h-[0.5px] bg-muted-foreground" />
                    <div className="grid grid-cols-4 gap-4">
                        <div className="grid grid-cols-1 gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center justify-center">
                                    <img
                                        src="/household_consumption.svg"
                                        alt="Logo 1"
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex items-center justify-center">
                                    <p className="text-xs text-gray-500">
                                        21.43%
                                    </p>
                                    <p className="text-sm font-medium">
                                        Of an american household weekly energy
                                        consumption
                                    </p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center justify-center">
                                    <img
                                        src="/transportation.svg"
                                        alt="Logo 2"
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex items-center justify-center">
                                    <p className="text-xs text-gray-500">123</p>
                                    <p className="text-sm font-medium">
                                        Kilometers ridden
                                    </p>
                                </div>
                            </div>
                            {/* Row 3 */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center justify-center">
                                    <img
                                        src="/tv.svg"
                                        alt="Logo 3"
                                        className="h-16 w-16"
                                    />
                                </div>
                                <div className="flex items-center justify-center">
                                    <p className="text-xs text-gray-500">
                                        14 DAYS
                                    </p>
                                    <p className="text-sm font-medium">
                                        Of watching TV
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="col-span-1">
                            <RadialChart data={RadialChartData.energy} />
                        </div>
                        <div className="col-span-1">
                            <RadialChart data={RadialChartData.emissions} />
                        </div>
                        <div className="col-span-1">
                            <RadialChart data={RadialChartData.duration} />
                        </div>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2 md:gap-8">
                        <ExperimentsBarChart params={ExperimentsData} />
                        <RunsScatterChart params={RunData} />
                    </div>
                </main>
            </div>
        );
    }
}
