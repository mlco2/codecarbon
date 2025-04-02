import { DateRangePicker } from "@/components/date-range-picker";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { SettingsIcon } from "lucide-react";
import Image from "next/image";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import EmissionsTimeSeriesChart from "@/components/emissions-time-series";
import RadialChart from "@/components/radial-chart";
import { ProjectDashboardProps } from "@/types/project-dashboard";
import { getDefaultDateRange } from "@/helpers/date-utils";
import { useState } from "react";
import CreateExperimentModal from "./createExperimentModal";

export default function ProjectDashboard({
    project,
    date,
    onDateChange,
    radialChartData,
    convertedValues,
    experimentsData,
    runData,
    selectedExperimentId,
    selectedRunId,
    onExperimentClick,
    onRunClick,
    onSettingsClick,
    organizationId,
}: ProjectDashboardProps) {
    const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

    const handleCreateExperimentClick = () => {
        setIsExperimentModalOpen(true);
    };

    const refreshExperimentList = async () => {
        // Logic to refresh experiments if needed
    };

    return (
        <div className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div className="flex flex-row gap-6">
                    <h1 className="text-2xl font-semi-bold">
                        Project {project.name}
                    </h1>
                    <Button
                        onClick={onSettingsClick}
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
                            onDateChange(newDate || getDefaultDateRange())
                        }
                    />
                </div>
                <Button
                    onClick={handleCreateExperimentClick}
                    className="bg-primary text-primary-foreground"
                >
                    + Add Experiment
                </Button>
                <CreateExperimentModal
                    projectId={project.id}
                    isOpen={isExperimentModalOpen}
                    onClose={() => setIsExperimentModalOpen(false)}
                    onExperimentCreated={refreshExperimentList}
                />
            </div>
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
                    onExperimentClick={onExperimentClick}
                />
                <RunsScatterChart
                    params={{
                        ...runData,
                        experimentId: selectedExperimentId,
                    }}
                    onRunClick={onRunClick}
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
        </div>
    );
}
