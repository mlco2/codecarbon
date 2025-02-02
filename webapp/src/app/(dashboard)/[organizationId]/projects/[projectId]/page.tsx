"use client";

import { useState, useEffect, useCallback, use } from "react";
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
import { getProjectEmissionsByExperiment } from "@/server-functions/experiments";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import CreateExperimentModal from "@/components/createExperimentModal";
import Image from "next/image";

// Fonction pour obtenir la plage de dates par défaut
const getDefaultDateRange = (): { from: Date; to: Date } => {
    const today = new Date();
    return {
        from: startOfDay(addMonths(today, -2)),
        to: endOfDay(today),
    };
};

export default function ProjectPage({
    params,
}: Readonly<{
    params: Promise<{
        projectId: string;
        organizationId: string;
    }>;
}>) {
    const { projectId, organizationId } = use(params);

    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);

    useEffect(() => {
        // Replace with your actual API endpoint
        const fetchProjectDetails = async () => {
            try {
                const project: Project = await getOneProject(projectId);
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
            }
        };

        fetchProjectDetails();
    }, [projectId]);
    const router = useRouter();
    const handleSettingsClick = () => {
        router.push(`/${organizationId}/projects/${projectId}/settings`);
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
        projectId: projectId,
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });
    const [runData, setRunData] = useState({
        experimentId: "",
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
    });
    const [convertedValues, setConvertedValues] = useState({
        citizen: "0",
        transportation: "0",
        tvTime: "0",
    });
    const [selectedExperimentId, setSelectedExperimentId] =
        useState<string>("");
    const [selectedRunId, setSelectedRunId] = useState<string>("");

    const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

    const handleCreateExperimentClick = () => {
        setIsExperimentModalOpen(true);
    };

    const refreshExperimentList = async () => {
        // Logic to refresh experiments if needed
    };

    useEffect(() => {
        async function fetchData() {
            const report = await getProjectEmissionsByExperiment(
                projectId,
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
                projectId: projectId,
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
                citizen: getEquivalentCitizenPercentage(
                    newRadialChartData.emissions.value,
                ).toFixed(2),
                transportation: getEquivalentCarKm(
                    newRadialChartData.emissions.value,
                ).toFixed(2),
                tvTime: getEquivalentTvTime(
                    newRadialChartData.energy.value,
                ).toFixed(2),
            });
        }

        fetchData();
    }, [projectId, date]);

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
                    <div className="flex gap-4">
                        <DateRangePicker
                            date={date}
                            onDateChange={(newDate) =>
                                setDate(newDate || getDefaultDateRange())
                            }
                        />
                        <Button
                            onClick={handleCreateExperimentClick}
                            className="bg-primary text-primary-foreground"
                        >
                            + Add Experiment
                        </Button>
                        <CreateExperimentModal
                            projectId={projectId}
                            isOpen={isExperimentModalOpen}
                            onClose={() => setIsExperimentModalOpen(false)}
                            onExperimentCreated={refreshExperimentList}
                        />
                    </div>
                </div>
                <Separator className="h-[0.5px] bg-muted-foreground" />
                <div className="grid grid-cols-4 gap-4">
                    <div className="grid grid-cols-1 gap-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="flex items-center justify-center">
                                <Image
                                    src="/household_consumption.svg"
                                    alt="Household consumption icon"
                                    width={64}
                                    height={64}
                                    className="h-16 w-16"
                                />
                            </div>
                            <div className="flex flex-col col-span-2 justify-center">
                                <p className="text-4xl text-primary">
                                    {convertedValues.citizen} %
                                </p>
                                <p className="text-sm font-medium">
                                    Of a U.S citizen weekly energy emissions
                                </p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="flex items-center justify-center">
                                <Image
                                    src="/transportation.svg"
                                    alt="Transportation icon"
                                    width={64}
                                    height={64}
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
                                <Image
                                    src="/tv.svg"
                                    alt="TV icon"
                                    width={64}
                                    height={64}
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

                <Separator className="h-[0.5px] bg-muted-foreground" />
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
                <Separator className="h-[0.5px] bg-muted-foreground" />
                <div className="grid gap-4 md:grid-cols-1 md:gap-8">
                    {selectedRunId && (
                        <>
                            <EmissionsTimeSeriesChart runId={selectedRunId} />
                            <Separator className="h-[0.5px] bg-muted-foreground" />
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
