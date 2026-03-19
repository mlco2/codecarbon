import { lazy, Suspense, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const RadialChart = lazy(() => import("@/components/radial-chart"));

import {
  getEquivalentCarKm,
  getEquivalentCitizenPercentage,
  getEquivalentTvTime,
} from "@/helpers/constants";
import {
  THIRTY_DAYS_MS,
  SECONDS_PER_DAY,
} from "@/helpers/time-constants";
import { fetcher } from "@/api/swr";
import { getOrganizationEmissionsByProject } from "@/api/organizations";
import { Organization, OrganizationReport } from "@/api/schemas";
import { DateRange } from "react-day-picker";
import useSWR from "swr";

export default function OrgDashboardPage() {
  const { organizationId } = useParams<{ organizationId: string }>();
  const {
    data: organization,
    isLoading,
    error,
  } = useSWR<Organization>(`/organizations/${organizationId}`, fetcher);

  const today = new Date();
  const [date, setDate] = useState<DateRange | undefined>({
    from: new Date(today.getTime() - THIRTY_DAYS_MS),
    to: today,
  });
  const [organizationReport, setOrganizationReport] = useState<
    OrganizationReport | undefined
  >({ name: "", duration: 0, emissions: 0, energy_consumed: 0 });

  useEffect(() => {
    async function fetchOrganizationReport() {
      try {
        const report = await getOrganizationEmissionsByProject(
          organizationId!,
          date,
        );
        if (report) {
          setOrganizationReport(report);
        }
      } catch (error) {
        console.error("Failed to fetch organization report:", error);
      }
    }
    fetchOrganizationReport();
  }, [organizationId, date]);

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
            (organizationReport.duration / SECONDS_PER_DAY).toFixed(2),
          )
        : 0,
    },
  };

  const citizen_converted_value = getEquivalentCitizenPercentage(
    RadialChartData.emissions.value,
  ).toFixed(2);
  const transportation_converted_value = getEquivalentCarKm(
    RadialChartData.emissions.value,
  ).toFixed(2);
  const tv_time_converted_value = getEquivalentTvTime(
    RadialChartData.energy.value,
  ).toFixed(2);

  const radialFallback = (
    <Card className="flex flex-col h-full items-center justify-center">
      <CardContent className="p-0">
        <Skeleton className="h-44 w-44 rounded-full" />
      </CardContent>
    </Card>
  );

  return (
    <div className="h-full w-full overflow-auto">
      {!organization && <ErrorMessage />}
      {organization && (
        <div className="flex flex-col gap-4 p-4 md:gap-8 md:p-8">
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col items-center justify-center">
              <img
                src="/icons/household_consumption.svg"
                alt="Household consumption icon"
                width={64}
                height={64}
                className="h-16 w-16"
              />
              <p className="text-xs text-muted-foreground">
                {citizen_converted_value} %
              </p>
              <p className="text-sm font-medium">
                Of a U.S citizen weekly energy emissions
              </p>
            </div>
            <div className="flex flex-col items-center justify-center">
              <img
                src="/icons/transportation.svg"
                alt="Transportation icon"
                width={64}
                height={64}
                className="h-16 w-16"
              />
              <p className="text-xs text-muted-foreground">
                {transportation_converted_value}
              </p>
              <p className="text-sm font-medium">Kilometers ridden</p>
            </div>
            <div className="flex flex-col items-center justify-center">
              <img
                src="/icons/tv.svg"
                alt="TV icon"
                width={64}
                height={64}
                className="h-16 w-16"
              />
              <p className="text-xs text-muted-foreground">
                {tv_time_converted_value} days
              </p>
              <p className="text-sm font-medium">Of watching TV</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Suspense fallback={radialFallback}>
              <RadialChart data={RadialChartData.energy} />
            </Suspense>
            <Suspense fallback={radialFallback}>
              <RadialChart data={RadialChartData.emissions} />
            </Suspense>
            <Suspense fallback={radialFallback}>
              <RadialChart data={RadialChartData.duration} />
            </Suspense>
          </div>
        </div>
      )}
    </div>
  );
}
