//////////////////////////////////////////////////////////////////////////////
// EMISSIONS KGCO2 EQUIVALENT
//////////////////////////////////////////////////////////////////////////////

// Source: https://www.iea.org/data-and-statistics/charts/co2-total-emissions-per-capita-by-region-2000-2023
const US_CITIZEN_YEARLY_EMISSIONS = 13300; // KgCO2.eq
const US_CITIZEN_WEEKLY_EMISSIONS = US_CITIZEN_YEARLY_EMISSIONS / 52; // KgCO2.eq

/**
 *
 * @param emissionKg Emission in KgCO2
 * @returns Equivalent percentage of an american citizen weekly energy consumption
 */
export const getEquivalentCitizenPercentage = (emissionKg: number) => {
    return (
        Math.round(((100 * emissionKg) / US_CITIZEN_WEEKLY_EMISSIONS) * 100) /
        100
    );
};

// Average emissions of a european car : 133 gCO2.eq / km for a new car using gasoline in Europe in 2023.
// Source: https://co2cars.apps.eea.europa.eu/?source=%7B%22track_total_hits%22%3Atrue%2C%22query%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22constant_score%22%3A%7B%22filter%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22bool%22%3A%7B%22should%22%3A%5B%7B%22term%22%3A%7B%22year%22%3A2023%7D%7D%5D%7D%7D%2C%7B%22bool%22%3A%7B%22should%22%3A%5B%7B%22term%22%3A%7B%22scStatus%22%3A%22Provisional%22%7D%7D%5D%7D%7D%5D%7D%7D%7D%7D%5D%7D%7D%2C%22display_type%22%3A%22tabular%22%7D
const CAR_EMISSIONS_KGCO2_PER_KM = 133 / 1000;
/**
 *
 * @param emissionKg Emission in KgCO2
 * @returns Equivalent Km ridden by a car
 */
export const getEquivalentCarKm = (emissionKg: number) => {
    return Math.round((emissionKg / CAR_EMISSIONS_KGCO2_PER_KM) * 100) / 100;
};

//////////////////////////////////////////////////////////////////////////////
// ENERGY CONSUMPTION
//////////////////////////////////////////////////////////////////////////////

//  Average TV consumption : (187_000 Wh_per_year / (365*24)) * 6.5 h_per_day = 138 Wh
// Source : https://agirpourlatransition.ademe.fr/particuliers/maison/economies-denergie-deau/electricite-combien-consomment-appareils-maison
const TV_ENERGY_PER_DAY_KWH = (138 / 1000) * 24;
/**
 *
 * @param energyKwh Energy consumed in KWh
 * @returns TV time equivalent in days
 */
export const getEquivalentTvTime = (energyKwh: number): number => {
    return Math.round((energyKwh / TV_ENERGY_PER_DAY_KWH) * 100) / 100;
};
