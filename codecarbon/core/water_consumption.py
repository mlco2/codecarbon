"""
Provides functionality to compute the water consumed to generate the
electricity used by the compute, for cloud & private infra.

This is the *indirect* water consumption (water evaporated or consumed by
power plants to generate electricity), estimated from the energy mix of the
country or region where the compute runs. The *direct* water consumption of
a data center (cooling) is covered by the ``wue`` parameter of the trackers.
"""

from typing import Dict, Optional, Tuple

from codecarbon.core.units import Energy, WaterPerKWh
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.external.logger import logger
from codecarbon.input import DataSource


class WaterConsumption:
    # Fraction of the electricity production that must be covered by
    # per-source water data before we trust the computed intensity. Below
    # this threshold we fall back to the world average.
    MIN_ENERGY_MIX_COVERAGE = 0.9

    # Map of the source names of regional energy mix files (e.g.
    # canada_energy_mix.json) to the source names of
    # water_consumption_per_source.json
    REGION_SOURCE_TO_WATER_SOURCE = {
        "coal": "coal",
        "petroleum": "oil",
        "naturalGas": "gas",
        "nuclear": "nuclear",
        "hydro": "hydroelectricity",
        "biomass": "biofuel",
        "solar": "solar",
        "wind": "wind",
    }

    def __init__(self, data_source: DataSource):
        self._data_source = data_source
        # The water intensity is constant for a given location: cache it so
        # it is not recomputed, and its warnings not re-logged, on every
        # measurement cycle.
        self._intensity_cache: Dict[
            Tuple[Optional[str], Optional[str]], WaterPerKWh
        ] = {}

    def get_cloud_water_consumption(
        self, energy: Energy, cloud: CloudMetadata, geo: Optional[GeoMetadata] = None
    ) -> float:
        """
        Computes water consumption for cloud infra.
        Cloud providers do not publish per-region water usage data, so the
        water intensity of the electricity of the country hosting the
        machine is used when known, else the world average.
        :param energy: Energy consumed by the process (kWh)
        :param cloud: Cloud provider and region of compute
        :param geo: Instance of GeoMetadata to fall back on
        :return: water consumption in L
        """
        if geo:
            return self.get_private_infra_water_consumption(energy, geo)
        return self._world_average_water_intensity().l_per_kWh * energy.kWh

    def get_private_infra_water_consumption(
        self, energy: Energy, geo: GeoMetadata
    ) -> float:
        """
        Computes water consumption for private infra.
        :param energy: Energy consumed by the process (kWh)
        :param geo: Country and region metadata
        :return: water consumption in L
        """
        cache_key = (geo.country_iso_code, geo.region)
        water_per_kWh = self._intensity_cache.get(cache_key)
        if water_per_kWh is None:
            water_per_kWh = self._get_water_intensity(geo)
            self._intensity_cache[cache_key] = water_per_kWh
        return water_per_kWh.l_per_kWh * energy.kWh  # L

    def get_region_water_consumption(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes water consumption for a region on private infra,
        using the regional energy mix when available.
        :param energy: Energy consumed by the process (kWh)
        :param geo: Country and region metadata
        :return: water consumption in L
        """
        return self._region_water_intensity(geo).l_per_kWh * energy.kWh  # L

    def get_country_water_consumption(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes water consumption for a country on private infra,
        using the mix of energy sources of that country.
        :param energy: Energy consumed by the process (kWh)
        :param geo: Country and region metadata
        :return: water consumption in L
        """
        return self._country_water_intensity(geo).l_per_kWh * energy.kWh  # L

    def _get_water_intensity(self, geo: GeoMetadata) -> WaterPerKWh:
        country_iso_code = (
            geo.country_iso_code.upper() if geo.country_iso_code is not None else None
        )
        # Canada is the only country with a regional energy mix data file.
        # The USA regional data is at the emissions level, not the energy
        # mix level, so it cannot be used for water.
        compute_with_regional_data: bool = (geo.region is not None) and (
            country_iso_code == "CAN"
        )

        if compute_with_regional_data:
            try:
                return self._region_water_intensity(geo)
            except Exception as e:
                logger.debug(
                    f"Regional water intensity retrieval failed ({e})."
                    + " Falling back on the country water intensity."
                )
        return self._country_water_intensity(geo)

    def _region_water_intensity(self, geo: GeoMetadata) -> WaterPerKWh:
        country_energy_mix_data = self._data_source.get_country_energy_mix_data(
            geo.country_iso_code.lower()
        )
        energy_mix = country_energy_mix_data[geo.region]
        return self._energy_mix_to_water_intensity(
            energy_by_water_source={
                water_source: energy_mix.get(source)
                for source, water_source in self.REGION_SOURCE_TO_WATER_SOURCE.items()
            },
            energy_sum=energy_mix["total"],
            place=f"the region {geo.region}",
        )

    def _country_water_intensity(self, geo: GeoMetadata) -> WaterPerKWh:
        energy_mix = self._data_source.get_global_energy_mix_data()

        if geo.country_iso_code not in energy_mix:
            logger.warning(
                f"We do not have water data for {geo.country_iso_code},"
                " using world average water intensity."
            )
            return self._world_average_water_intensity()

        country_energy_mix: Dict = energy_mix[geo.country_iso_code]
        # Iterate through the primary sources of energy in the country.
        # Aggregated sources of global_energy_mix.json (fossil, renewables,
        # low_carbon...) have no entry in water_consumption_per_source.json,
        # so they are skipped and no energy is counted twice.
        water_per_kWh = self._energy_mix_to_water_intensity(
            energy_by_water_source={
                source[: -len("_TWh")]: energy_per_year
                for source, energy_per_year in country_energy_mix.items()
                if source.endswith("_TWh")
            },
            energy_sum=country_energy_mix["total_TWh"],
            place=str(geo.country_name),
        )
        logger.debug(
            f"We apply a water intensity of {water_per_kWh.l_per_kWh:.3f}"
            + f" L/kWh for {geo.country_name}"
        )
        return water_per_kWh

    def _energy_mix_to_water_intensity(
        self,
        energy_by_water_source: Dict[str, Optional[float]],
        energy_sum: float,
        place: str,
    ) -> WaterPerKWh:
        """
        Convert a mix of electricity sources into water consumed per kWh of
        electricity, as the weighted average of the water consumption of the
        sources with known water data.
        :param energy_by_water_source: energy produced, keyed by the source
            names of water_consumption_per_source.json. Sources with no
            water data or a None energy are ignored.
        :param energy_sum: total energy produced, in the same unit
        :param place: name of the country or region, for logging
        :return: a WaterPerKWh object representing the average water
            intensity in L/kWh
        """
        if not energy_sum:
            logger.warning(
                f"No total energy production for {place}, using world average"
                " water intensity."
            )
            return self._world_average_water_intensity()

        water_consumption_per_source = (
            self._data_source.get_water_consumption_per_source_data()
        )
        water_intensity = 0  # gal us / MWh, weighted by source share
        energy_sum_covered = 0
        for water_source, energy_for_source in energy_by_water_source.items():
            water_for_source = water_consumption_per_source.get(water_source)
            if water_for_source is not None and energy_for_source is not None:
                water_intensity += (energy_for_source / energy_sum) * water_for_source
                energy_sum_covered += energy_for_source

        coverage = energy_sum_covered / energy_sum
        if coverage < self.MIN_ENERGY_MIX_COVERAGE:
            logger.warning(
                f"Only {coverage:.0%} of the electricity produced in {place}"
                " comes from sources with known water intensity,"
                " using world average."
            )
            return self._world_average_water_intensity()

        # Attribute the average intensity of the covered sources to the
        # (small) uncovered share of the mix.
        return WaterPerKWh.from_gal_us_per_MWh(water_intensity / coverage)

    def _world_average_water_intensity(self) -> WaterPerKWh:
        water_consumption_per_source = (
            self._data_source.get_water_consumption_per_source_data()
        )
        return WaterPerKWh.from_gal_us_per_MWh(
            water_consumption_per_source["world_average"]
        )
