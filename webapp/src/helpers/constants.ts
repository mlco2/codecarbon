/**
 * The average U.S. household consumes about 10,500 kilowatthours (kWh) of electricity per year
 * 10 500 / 52 = 202 kWh per week
 * USA "carbon_intensity": 0.368102 KgCO2.eq / kWh
 */
const US_HOUSEHOLD_WEEKLY_EMISSIONS = 202 * 0.368102; // 74 KgCO2.eq
// American household weekly energy consumption
export const getEquivalentHouseHoldPercentage = (emissionKg: number) => {
    return (
        Math.round(((100 * emissionKg) / US_HOUSEHOLD_WEEKLY_EMISSIONS) * 100) /
        100
    );
};

// Average emissions of a european car : 130 gCO2.eq / km
const CAR_EMISSIONS_KGCO2_PER_KM = 130 / 1000;
export const getEquivalentCarKm = (emissionKg: number) => {
    return Math.round((emissionKg / CAR_EMISSIONS_KGCO2_PER_KM) * 100) / 100;
};

//  Average TV consumption : 100 W
//  Average carbon intensity : 0.475 KgCO2.eq/KWh
const TV_CO2_EMISSIONS_PER_MINUTE = ((100 / 1000) * 0.475) / 60;
export const getEquivalentTvTime = (emissionKg: number) => {
    return Math.round((emissionKg / TV_CO2_EMISSIONS_PER_MINUTE) * 100) / 100;
};
