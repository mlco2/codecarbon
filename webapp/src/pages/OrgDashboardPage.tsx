import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import { AddAPhotoIcon } from "@/components/icons/figma-icons";
import { DateRangePicker } from "@/components/date-range-picker";
import ConsumedEnergyGauge from "@/components/consumed-energy-gauge";

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
 * The Global dashboard from Figma frame 218:7838.
 *
 * The page is one fluid content column: a breadcrumb, a header, then two
 * sections below a rule. Its structure is expressed as flex regions with the
 * spacing on their parents, so it holds together at any width rather than only
 * at the frame's 1440x1024.
 *
 * Where the design's own measurements were internally inconsistent they have
 * been normalised to a single value, since they clearly describe one gutter:
 *   - the breadcrumb, rule and sections sit at x 178 / 170 / 163 in the frame;
 *     all three now share the container's horizontal padding
 *   - the three equivalence items have 26 / 22 / 21px icon gaps; all now use one
 *
 * Text metrics are untouched: the exact Figma families, weights and sizes live in
 * the `type-*` classes in globals.css, at line-height "normal" as the design
 * specifies. Vertical rhythm comes from gaps, so nothing depends on a pinned line
 * box and the layout holds as the display face loads.
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

    const equivalences = [
        {
            icon: "/icons/household_consumption.svg",
            alt: "Household consumption icon",
            value: `${getEquivalentCitizenPercentage(
                RadialChartData.emissions.value,
            ).toFixed(2)}%`,
            caption: "Of an american household weekly energy consumption",
        },
        {
            icon: "/icons/transportation.svg",
            alt: "Transportation icon",
            value: `${getEquivalentCarKm(
                RadialChartData.emissions.value,
            ).toFixed(2)} km`,
            caption: "Kilometers ridden",
        },
        {
            icon: "/icons/tv.svg",
            alt: "TV icon",
            value: `${getEquivalentTvTime(RadialChartData.energy.value).toFixed(
                2,
            )} days`,
            caption: "Of watching TV",
        },
    ];

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
            <div className="flex flex-col gap-8 pb-5 lg:gap-24 lg:pb-6">
                {/* Breadcrumb — Figma 218:14433 */}
                <nav
                    aria-label="Breadcrumb"
                    className="type-mono-medium type-breadcrumb"
                >
                    <span className="text-cc-breadcrumb-gray">
                        {organization.name}/
                    </span>
                    <span className="text-cc-button-hover">Global</span>
                </nav>

                {/* Header — Figma 218:14437 / 218:14436 / 218:14435 / 218:14532 */}
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
                (Figma 218:14434). */}
            <div className="flex flex-col gap-10 border-t border-cc-rule pt-6 lg:gap-20 lg:pt-8">
                {/* Equal to — Figma 218:14441 */}
                <section className="flex flex-col gap-6 lg:gap-heading">
                    <div className="flex items-center justify-between gap-4">
                        <h2 className="type-display type-section-title text-cc-white">
                            Equal to
                        </h2>
                        {/*
                         * Figma 218:14444. A plain vector frame in the design,
                         * not a component instance, with no prototype
                         * interaction — so there is no defined action behind it
                         * and the app has no matching feature. Rendered as drawn,
                         * non-interactive, rather than wired to a guess.
                         */}
                        <AddAPhotoIcon className="shrink-0 text-cc-breadcrumb-gray" />
                    </div>

                    {/*
                     * Figma distributes the three equivalences with
                     * space-between; they wrap instead of overflowing once the
                     * column is too narrow to hold them.
                     */}
                    <ul className="flex flex-wrap justify-between gap-x-12 gap-y-6 lg:gap-y-8">
                        {equivalences.map((item) => (
                            <li
                                key={item.caption}
                                className="flex min-w-0 items-center gap-4 lg:gap-6"
                            >
                                <img
                                    src={item.icon}
                                    alt={item.alt}
                                    width={50}
                                    height={50}
                                    className="size-10 shrink-0 lg:size-[50px]"
                                />
                                <div className="flex min-w-0 flex-col gap-2">
                                    <p className="type-display type-stat-value text-cc-lime">
                                        {item.value}
                                    </p>
                                    {/* Measure from the design, which wraps this caption to two lines. */}
                                    <p className="type-mono-medium type-stat-caption max-w-[15.5rem] text-cc-white">
                                        {item.caption}
                                    </p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </section>

                {/* Consumed energy — Figma 218:14513 */}
                <section className="flex flex-col gap-6 lg:gap-heading">
                    <h2 className="type-display type-section-title text-cc-white">
                        Consumed energy
                    </h2>
                    {/* Fixed-size gauges in a wrapping row, as the design lays
                        them out (a gap, not space-between). */}
                    <ul className="flex flex-wrap gap-6 lg:gap-9">
                        {gauges.map((gauge) => (
                            <li
                                key={gauge.label}
                                className="w-40 max-w-full sm:w-gauge"
                            >
                                <ConsumedEnergyGauge
                                    value={gauge.value}
                                    label={gauge.label}
                                />
                            </li>
                        ))}
                    </ul>
                </section>
            </div>
        </div>
    );
}
