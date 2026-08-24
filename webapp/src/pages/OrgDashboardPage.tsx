import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { DateRangePicker } from "@/components/date-range-picker";
import ConsumedEnergyGauges from "@/components/consumed-energy-gauges";
import EquivalenceList, { equivalences } from "@/components/equivalence-list";

import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "@/helpers/constants";
import { THIRTY_DAYS_MS, SECONDS_PER_DAY } from "@/helpers/time-constants";
import { fetcher } from "@/api/swr";
import { getOrganizationEmissionsByProject } from "@/api/organizations";
import { Organization, OrganizationReport } from "@/api/schemas";
import { DateRange } from "react-day-picker";
import useSWR from "swr";

/*
 * The Global dashboard: one fluid content column — a breadcrumb, a header, then
 * two sections below a rule — built as flex regions with the spacing on their
 * parents, so it holds at any width rather than only at the frame's 1440x1024.
 */
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

    if (!organization) {
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
            label: "Kg. Eq. CO2",
            value: organizationReport?.emissions
                ? parseFloat(organizationReport.emissions.toFixed(2))
                : 0,
        },
        duration: {
            label: "days",
            value: organizationReport?.duration
                ? parseFloat(
                      (organizationReport.duration / SECONDS_PER_DAY).toFixed(
                          2,
                      ),
                  )
                : 0,
        },
    };

    const equivalenceItems = equivalences({
        citizen: getEquivalentCitizenPercentage(
            RadialChartData.emissions.value,
        ).toFixed(2),
        transportation: getEquivalentCarKm(
            RadialChartData.emissions.value,
        ).toFixed(2),
        tvTime: getEquivalentTvTime(RadialChartData.energy.value).toFixed(2),
    });

    const gauges = [
        RadialChartData.energy,
        RadialChartData.emissions,
        RadialChartData.duration,
    ];

    return (
        /*
         * One scrolling content column. All horizontal placement comes from this
         * container's padding, and all vertical rhythm from the gaps between its
         * regions — so the rule, the header and the sections share a single
         * gutter instead of carrying three different Figma left offsets
         * (163 / 170 / 178px in the frame, normalised to one here).
         */
        <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-cc-page-background px-5 pb-10 pt-4 sm:px-10 lg:px-20 lg:pb-8 lg:pt-5">
            {/* Breadcrumb and header, with the space below them separating the
                group from the rule. */}
            <div className="flex flex-col gap-8 pb-5 lg:gap-16 lg:pb-6">
                {/* Breadcrumb */}
                <nav
                    aria-label="Breadcrumb"
                    className="type-mono-medium type-breadcrumb"
                >
                    <span className="text-cc-breadcrumb-gray">
                        {organization.name}/
                    </span>
                    <span className="text-cc-button-hover">Global</span>
                </nav>

                {/* Header */}
                <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-5 lg:gap-y-8">
                    <div className="flex min-w-0 flex-col gap-2">
                        <h1 className="type-display type-page-title text-cc-white">
                            {organization.name} Global
                        </h1>
                        <p className="type-mono-medium type-page-subtitle text-cc-white">
                            This section has the impact of all projects combined
                        </p>
                    </div>

                    {/* Bounded so the field keeps the design's proportions on wide
                    screens instead of stretching with the viewport. */}
                    <div className="w-full max-w-sm">
                        <DateRangePicker
                            variant="dashboard"
                            date={date as DateRange}
                            onDateChange={setDate}
                        />
                    </div>
                </header>
            </div>

            {/* Sections, separated from the header by the design's rule
                rule. */}
            <div className="flex flex-col gap-10 border-t border-cc-rule pt-6 lg:gap-20 lg:pt-8">
                {/* Equal to */}
                <section className="flex flex-col gap-6 lg:gap-heading">
                    <h2 className="type-display type-section-title text-cc-white">
                        Equal to
                    </h2>

                    <EquivalenceList items={equivalenceItems} />
                </section>

                {/* Consumed energy */}
                <section className="flex flex-col gap-6 lg:gap-heading">
                    <h2 className="type-display type-section-title text-cc-white">
                        Consumed energy
                    </h2>
                    <ConsumedEnergyGauges gauges={gauges} />
                </section>
            </div>
        </div>
    );
}
