import { DateRangePicker } from "@/components/date-range-picker";
import { Separator } from "@/components/ui/separator";
import Image from "next/image";
import ExperimentsBarChart from "@/components/experiment-bar-chart";
import RunsScatterChart from "@/components/runs-scatter-chart";
import EmissionsTimeSeriesChart from "@/components/emissions-time-series";
import RadialChart from "@/components/radial-chart";
import { PublicProjectDashboardProps } from "@/types/public-project-dashboard";
import { getDefaultDateRange } from "@/helpers/date-utils";

export default function PublicProjectDashboard({
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
}: PublicProjectDashboardProps) {
    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-bold">{project.name}</h1>
                    <p className="text-muted-foreground">{project.description}</p>
                </div>
                <div>
                    <DateRangePicker
                        date={date}
                        onDateChange={(newDate) =>
                            onDateChange(newDate || getDefaultDateRange())
                        }
                    />
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
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

            <Separator className="h-[0.5px] bg-muted-foreground my-8" />
            <div className="grid gap-8 md:grid-cols-2">
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
            {selectedRunId && (
                <>
                    <Separator className="h-[0.5px] bg-muted-foreground my-8" />
                    <div className="w-full">
                        <EmissionsTimeSeriesChart runId={selectedRunId} />
                    </div>
                </>
            )}
        </div>
    );
}