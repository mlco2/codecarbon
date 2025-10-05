import { ExperimentReport } from "@/types/experiment-report";
import {
    getEquivalentCarKm,
    getEquivalentCitizenPercentage,
    getEquivalentTvTime,
} from "./constants";
import { SECONDS_PER_DAY } from "./time-constants";

export type RadialChartData = {
    energy: { label: string; value: number };
    emissions: { label: string; value: number };
    duration: { label: string; value: number };
};

export type ConvertedValues = {
    citizen: string;
    transportation: string;
    tvTime: string;
};

/**
 * Calculate radial chart data from experiment reports
 */
export function calculateRadialChartData(
    report: ExperimentReport[],
): RadialChartData {
    return {
        energy: {
            label: "kWh",
            value: parseFloat(
                report
                    .reduce((n, { energy_consumed }) => n + energy_consumed, 0)
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
                        (n, { duration }) => n + duration / SECONDS_PER_DAY,
                        0,
                    )
                    .toFixed(2),
            ),
        },
    };
}

/**
 * Calculate converted equivalent values from radial chart data
 */
export function calculateConvertedValues(
    radialChartData: RadialChartData,
): ConvertedValues {
    return {
        citizen: getEquivalentCitizenPercentage(
            radialChartData.emissions.value,
        ).toFixed(2),
        transportation: getEquivalentCarKm(
            radialChartData.emissions.value,
        ).toFixed(2),
        tvTime: getEquivalentTvTime(radialChartData.energy.value).toFixed(2),
    };
}

/**
 * Get default radial chart data (all zeros)
 */
export function getDefaultRadialChartData(): RadialChartData {
    return {
        energy: { label: "kWh", value: 0 },
        emissions: { label: "kg eq CO2", value: 0 },
        duration: { label: "days", value: 0 },
    };
}

/**
 * Get default converted values (all zeros)
 */
export function getDefaultConvertedValues(): ConvertedValues {
    return {
        citizen: "0",
        transportation: "0",
        tvTime: "0",
    };
}
