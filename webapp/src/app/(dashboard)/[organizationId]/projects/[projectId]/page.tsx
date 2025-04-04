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
import {
    getExperiments,
    getProjectEmissionsByExperiment,
} from "@/server-functions/experiments";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import CreateExperimentModal from "@/components/createExperimentModal";
import { Card } from "@/components/ui/card";
import { TableBody, TableHeader, Table } from "@/components/ui/table";
import { Experiment } from "@/types/experiment";

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
    params: {
        projectId: string;
        organizationId: string;
    };
}>) {
    const [project, setProject] = useState({
        name: "",
        description: "",
    } as Project);
    const default_date = getDefaultDateRange();
    const [date, setDate] = useState<DateRange>(default_date);
    // The experiments of the current project. We need this because experimentReport only contains the experiments that have been run
    const [projectExperiments, setProjectExperiments] = useState<Experiment[]>(
        [],
    );
    // The reports (if any) of the experiments
    const [experimentReport, setExperimentReport] = useState<
        ExperimentReport[]
    >([]);
    const [radialChartData, setRadialChartData] = useState({
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
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
    const [experimentsBarCharData, setExperimentsBarCharData] = useState({
        projectId: params.projectId,
        startDate: default_date.from.toISOString(),
        endDate: default_date.to.toISOString(),
        selectedExperimentId: selectedExperimentId,
    });
    const [selectedRunId, setSelectedRunId] = useState<string>("");
    const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

    const router = useRouter();
    const handleSettingsClick = () => {
        router.push(
            `/${params.organizationId}/projects/${params.projectId}/settings`,
        );
    };

    const handleCreateExperimentClick = () => {
        setIsExperimentModalOpen(true);
    };

    const refreshExperimentList = useCallback(async () => {
        // Logic to refresh experiments if needed
        const experiments: Experiment[] = await getExperiments(
            params.projectId,
        );
        setProjectExperiments(experiments);
    }, []);

    /** Use effect functions */
    useEffect(() => {
        const fetchProjectDetails = async () => {
            try {
                const project: Project = await getOneProject(params.projectId);
                setProject(project);
            } catch (error) {
                console.error("Error fetching project description:", error);
            }
        };

        fetchProjectDetails();
        refreshExperimentList();
    }, [params.projectId, refreshExperimentList]);
    // Fetch the experiment report of the current project
    useEffect(() => {
        async function fetchData() {
            const report = await getProjectEmissionsByExperiment(
                params.projectId,
                date,
            );
            setExperimentReport(report);
        }

        fetchData();
    }, [params.projectId, date]);
    // Show the experiment report of the selected experiment. This is not in the same useEffect as the previous one because
    // we refresh the component data when we select an experiment but we don't want to do a call to refresh the data
    useEffect(() => {
        async function fetchData() {
            const newRadialChartData = {
                energy: {
                    label: "kWh",
                    value: parseFloat(
                        experimentReport
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
                        experimentReport
                            .reduce((n, { emissions }) => n + emissions, 0)
                            .toFixed(2),
                    ),
                },
                duration: {
                    label: "days",
                    value: parseFloat(
                        experimentReport
                            .reduce(
                                (n, { duration }) => n + duration / 86400,
                                0,
                            )
                            .toFixed(2),
                    ),
                },
            };
            setRadialChartData(newRadialChartData);

            setExperimentsBarCharData({
                projectId: params.projectId,
                selectedExperimentId: selectedExperimentId ?? "",
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

            setRunData({
                experimentId: selectedExperimentId ?? "",
                startDate: date?.from?.toISOString() ?? "",
                endDate: date?.to?.toISOString() ?? "",
            });

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
    }, [params.projectId, date, experimentReport, selectedExperimentId]);

    const handleExperimentRowClick = useCallback(
        (experimentId: string | undefined) => {
            if (!experimentId) return;
            setSelectedExperimentId(experimentId);
        },
        [],
    );
    const handleExperimentBarClick = useCallback(
        (experimentId: string) => {
            if (experimentId === selectedExperimentId) {
                setSelectedExperimentId("");
                return;
            }
            setSelectedExperimentId(experimentId);
        },
        [selectedExperimentId],
    );

    const handleRunClick = useCallback(
        (runId: string) => {
            if (runId === selectedRunId) {
                setSelectedRunId("");
                return;
            }
            setSelectedRunId(runId);
        },
        [selectedRunId],
    );

    return (
        <div className="h-full w-full overflow-auto">
            <main className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-semi-bold">
                            Project {project.name}
                        </h1>
                        <div className="flex items-center gap-2">
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
                    </div>
                    <div className="flex gap-4">
                        <DateRangePicker
                            date={date}
                            onDateChange={(newDate) =>
                                setDate(newDate || getDefaultDateRange())
                            }
                        />
                        <CreateExperimentModal
                            projectId={params.projectId}
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
                                <img
                                    src="/household_consumption.svg"
                                    alt="Logo 1"
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
                <Separator className="h-[0.5px] bg-muted-foreground" />
                <Card className="flex flex-col md:flex-row justify-start gap-4 px-4 py-4 w-full max-w-3/4">
                    <div className="flex items-center justify-start px-2">
                        <p className="text-sm font-medium pr-2 text-center">
                            {projectExperiments.length === 0
                                ? "No experiments have been created yet."
                                : "Set of experiments included in this project"}
                        </p>
                        <div className="flex items-center justify-center px-2">
                            <Button
                                onClick={handleCreateExperimentClick}
                                className="bg-primary text-primary-foreground"
                            >
                                + Add Experiment
                            </Button>
                        </div>
                    </div>
                    {projectExperiments.length !== 0 && (
                        <Card className="flex flex-col md:flex-row justify-between md:items-center gap-4 py-4 px-4 w-full max-w-3/4">
                            <Table>
                                <TableHeader>
                                    <tr>
                                        <th className="text-left">
                                            Experiment
                                        </th>
                                        <th className="text-left">
                                            Description
                                        </th>
                                        <th className="text-left">
                                            Experiment id
                                        </th>
                                    </tr>
                                </TableHeader>
                                <TableBody>
                                    {projectExperiments.map((experiment) => (
                                        <tr
                                            key={experiment.id}
                                            className={`cursor-pointer hover:bg-muted/50 ${
                                                experiment.id ===
                                                selectedExperimentId
                                                    ? "bg-primary/10"
                                                    : ""
                                            }`}
                                            onClick={() =>
                                                handleExperimentRowClick(
                                                    experiment.id,
                                                )
                                            }
                                        >
                                            <td>{experiment.name}</td>
                                            <td>{experiment.description}</td>
                                            <td>{experiment.id}</td>
                                        </tr>
                                    ))}
                                </TableBody>
                            </Table>
                        </Card>
                    )}
                </Card>

                <div className="grid gap-4 md:grid-cols-2 md:gap-8">
                    <ExperimentsBarChart
                        params={experimentsBarCharData}
                        onExperimentClick={handleExperimentBarClick}
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
                    {selectedRunId && selectedRunId !== "" && (
                        <>
                            <EmissionsTimeSeriesChart runId={selectedRunId} />
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
