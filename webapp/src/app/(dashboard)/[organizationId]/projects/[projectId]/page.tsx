"use client";

import { useState, useEffect, useCallback } from "react";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import EmissionsTimeSeriesChart from "@/components/emissions-time-series";
import RadialChart from "@/components/radial-chart";
import { Separator } from "@/components/ui/separator";
import { ExperimentReport } from "@/types/experiment-report";
import { DateRange } from "react-day-picker";
import { DateRangePicker } from "@/components/date-range-picker";
import { addMonths, startOfDay, endOfDay } from "date-fns";
import { useRouter } from "next/navigation";
import { SettingsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getOneProject } from "@/server-functions/projects";
import { Project } from "@/types/project";

// Fonction pour obtenir la plage de dates par défaut
const getDefaultDateRange = (): { from: Date; to: Date } => {
    const today = new Date();
    return {
        from: startOfDay(addMonths(today, -2)),
        to: endOfDay(today),
    };
};

async function getProjectEmissionsByExperiment(
    projectId: string,
    dateRange: DateRange,
): Promise<ExperimentReport[]> {
    let url = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/experiments/sums`;

    if (dateRange?.from || dateRange?.to) {
        const params = new URLSearchParams();
        if (dateRange.from) {
            params.append("start_date", dateRange.from.toISOString());
        }
        if (dateRange.to) {
            params.append("end_date", dateRange.to.toISOString());
        }
        url += `?${params.toString()}`;
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

export default function ProjectPage({
    params,
}: Readonly<{
    params: {
        projectId: string;
        organizationId: string;
    };
}>) {
    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);

    useEffect(() => {
        // Replace with your actual API endpoint
        const fetchProjectDetails = async () => {
            try {
                const project: Project = await getOneProject(params.projectId);
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
            }
        };

        fetchProjectDetails();
    }, []);
    const router = useRouter();
    const handleSettingsClick = () => {
        router.push(
            `/${params.organizationId}/projects/${params.projectId}/settings`,
        );
    };

    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);
    const [experimentReport, setExperimentReport] = useState<
        ExperimentReport[]
    >([]);
    const [radialChartData, setRadialChartData] = useState({
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    });
    const [experimentsData, setExperimentsData] = useState({
        projectId: params.projectId,
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });
    const [runData, setRunData] = useState({
        experimentId: "",
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });
    const [convertedValues, setConvertedValues] = useState({
        household: "0",
        transportation: "0",
        tvTime: "0",
    });
    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    useEffect(() => {
        async function fetchData() {
            const report = await getProjectEmissionsByExperiment(
                params.projectId,
                date,
            );
            setExperimentReport(report);

            const newRadialChartData = {
                energy: {
                    label: "kWh",
                    value: parseFloat(
                        report
                            .reduce(
                                (n, { energy_consumed }) => n + energy_consumed,
                                0,
                            )
                            .toFixed(2),
                    ),
                },
                emissions: {
                    label: "kg eq CO2",
                    value: parseFloat(
                        report
                            .reduce((n, { emissions }) => n + emissions, 0)
                            .toFixed(2),
                    ),
                },
                duration: {
                    label: "days",
                    value: parseFloat(
                        report
                            .reduce(
                                (n, { duration }) => n + duration / 86400,
                                0,
                            )
                            .toFixed(2),
                    ),
                },
            };
            setRadialChartData(newRadialChartData);

            setExperimentsData({
                projectId: params.projectId,
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

            setRunData({
                experimentId: report[0]?.experiment_id ?? "",
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

            setSelectedExperimentId(report[0]?.experiment_id ?? "");

            setConvertedValues({
                household: (
                    (newRadialChartData.emissions.value * 100) /
                    160.58
                ).toFixed(2),
                transportation: (
                    newRadialChartData.emissions.value / 0.409
                ).toFixed(2),
                tvTime: (
                    newRadialChartData.emissions.value /
                    (0.097 * 24)
                ).toFixed(2),
            });
        }

        fetchData();
    }, [params.projectId, date]);

    const handleExperimentClick = useCallback((experimentId: string) => {
        setSelectedExperimentId(experimentId);
        setRunData((prevData) => ({
            ...prevData,
            experimentId: experimentId,
        }));
        setSelectedRunId(""); // Réinitialiser le runId sélectionné
    }, []);

    const handleRunClick = useCallback((runId: string) => {
        setSelectedRunId(runId);
    }, []);

    return (
        <div className="h-full w-full overflow-auto">
            <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-semi-bold">
                            Project {project.name}
                        </h1>
                        <Button
                            onClick={handleSettingsClick}
                            variant="ghost"
                            size="icon"
                            className="rounded-full"
                        >
                            <SettingsIcon />
                        </Button>
                        <span className="text-sm font-semi-bold">
                            {project.description}
                        </span>
                    </div>
                    <div>
                        <DateRangePicker
                            date={date}
                            onDateChange={(newDate) =>
                                setDate(newDate || getDefaultDateRange())
                            }
                        />
                    </div>
                </div>
                <Separator className="h-[0.5px] bg-muted-foreground" />
                <div className="grid grid-cols-4 gap-4">
                    <div className="grid grid-cols-1 gap-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="flex items-center justify-center">
                                <img
                                    src="/household_consumption.svg"
                                    alt="Logo 1"
                                    className="h-16 w-16"
                                />
                            </div>
                            <div className="flex flex-col col-span-2 justify-center">
                                <p className="text-4xl text-primary">
                                    {convertedValues.household} %
                                </p>
                                <p className="text-sm font-medium">
                                    Of an american household weekly energy
                                    consumption
                                </p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="flex items-center justify-center">
                                <img
                                    src="/transportation.svg"
                                    alt="Logo 2"
                                    className="h-16 w-16"
                                />
                            </div>
                            <div className="flex flex-col col-span-2 justify-center">
                                <p className="text-4xl text-primary">
                                    {convertedValues.transportation}
                                </p>
                                <p className="text-sm font-medium">
                                    Kilometers ridden
                                </p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="flex items-center justify-center">
                                <img
                                    src="/tv.svg"
                                    alt="Logo 3"
                                    className="h-16 w-16"
                                />
                            </div>
                            <div className="flex flex-col col-span-2 justify-center">
                                <p className="text-4xl text-primary">
                                    {convertedValues.tvTime} days
                                </p>
                                <p className="text-sm font-medium">
                                    Of watching TV
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="col-span-1">
                        <RadialChart data={radialChartData.energy} />
                    </div>
                    <div className="col-span-1">
                        <RadialChart data={radialChartData.emissions} />
                    </div>
                    <div className="col-span-1">
                        <RadialChart data={radialChartData.duration} />
                    </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2 md:gap-8">
                    <ExperimentsBarChart
                        params={experimentsData}
                        onExperimentClick={handleExperimentClick}
                    />
                    <RunsScatterChart
                        params={{
                            ...runData,
                            experimentId: selectedExperimentId,
                        }}
                        onRunClick={handleRunClick}
                    />
                </div>
                <div className="grid gap-4 md:grid-cols-1 md:gap-8">
                    {selectedRunId && (
                        <EmissionsTimeSeriesChart runId={selectedRunId} />
                    )}
                </div>
            </main>
        </div>
    );
}
