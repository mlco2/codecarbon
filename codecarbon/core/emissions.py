"""
Provides functionality to compute emissions for cloud & private infra
based on impact & energy Usage package

https://github.com/mlco2/impact
https://github.com/responsibleproblemsolving/energy-usage
"""

from typing import Dict, Optional

import pandas as pd

from codecarbon.core import co2_signal
from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.external.logger import logger
from codecarbon.input import DataSource, DataSourceException


class Emissions:
    def __init__(
        self, data_source: DataSource, co2_signal_api_token: Optional[str] = None
    ):
        self._data_source = data_source
        self._co2_signal_api_token = co2_signal_api_token

    def get_cloud_emissions(self, energy: Energy, cloud: CloudMetadata) -> float:
        """
        Computes emissions for cloud infra
        :param energy: Mean power consumption of the process (kWh)
        :param cloud: Region of compute
        :return: CO2 emissions in kg
        """

        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()

        emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
            df.loc[(df["provider"] == cloud.provider) & (df["region"] == cloud.region)][
                "impact"
            ].item()
        )

        return emissions_per_kWh.kgs_per_kWh * energy.kWh  # kgs

    def get_cloud_country_name(self, cloud: CloudMetadata) -> str:
        """
        Returns the Country Name where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        return df.loc[
            (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        ]["country_name"].item()

    def get_cloud_country_iso_code(self, cloud: CloudMetadata) -> str:
        """
        Returns the Country ISO Code where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        return df.loc[
            (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        ]["countryIsoCode"].item()

    def get_cloud_geo_region(self, cloud: CloudMetadata) -> str:
        """
        Returns the State/City where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        state = df.loc[
            (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        ]["state"].item()
        if state is not None:
            return state
        city = df.loc[
            (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        ]["city"].item()
        return city

    def get_private_infra_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for private infra
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: CO2 emissions in kg
        """
        if self._co2_signal_api_token:
            try:
                return co2_signal.get_emissions(energy, geo, self._co2_signal_api_token)
            except Exception as e:
                logger.error(
                    "co2_signal.get_emissions: "
                    + str(e)
                    + " >>> Using CodeCarbon's data."
                )

        compute_with_regional_data: bool = (geo.region is not None) and (
            geo.country_iso_code.upper() in ["USA", "CAN"]
        )

        if compute_with_regional_data:
            try:
                return self.get_region_emissions(energy, geo)
            except Exception as e:
                logger.error(e, exc_info=True)
                logger.warning(
                    "Regional emissions retrieval failed."
                    + " Falling back on country emissions."
                )
        return self.get_country_emissions(energy, geo)

    def get_region_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for a region on private infra.
        Given an quantity of power consumed, use regional data
         on emissions per unit power consumed or the mix of energy sources.
        https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata.
        :return: CO2 emissions in kg
        """
        try:
            country_emissions_data = self._data_source.get_country_emissions_data(
                geo.country_iso_code.lower()
            )

            if geo.region not in country_emissions_data:
                # TODO: Deal with missing data, default to something
                raise ValueError(
                    f"Region: {geo.region} not found for Country"
                    + f" with ISO CODE : {geo.country_iso_code}"
                )

            emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_lbs_per_mWh(
                country_emissions_data[geo.region]["emissions"]
            )
        except DataSourceException:
            # This country has regional data at the energy mix level,
            # not the emissions level
            country_energy_mix_data = self._data_source.get_country_energy_mix_data(
                geo.country_iso_code.lower()
            )
            region_energy_mix_data = country_energy_mix_data[geo.region]
            emissions_per_kWh = self._region_energy_mix_to_emissions_rate(
                region_energy_mix_data
            )

        return emissions_per_kWh.kgs_per_kWh * energy.kWh  # kgs

    def get_country_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for a country on private infra,
        given a quantity of power consumed by
        using data for the mix of energy sources of that country.
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: CO2 emissions in kg
        """
        energy_mix = self._data_source.get_global_energy_mix_data()

        if geo.country_iso_code not in energy_mix:
            logger.warning(
                f"We do not have data for {geo.country_iso_code}, using world average."
            )
            carbon_intensity_per_source = (
                DataSource().get_carbon_intensity_per_source_data()
            )
            return (
                EmissionsPerKWh.from_g_per_kWh(
                    carbon_intensity_per_source.get("world_average")
                ).kgs_per_kWh
                * energy.kWh
            )  # kgs

        country_energy_mix: Dict = energy_mix[geo.country_iso_code]

        emissions_per_kWh = self._global_energy_mix_to_emissions_rate(
            country_energy_mix
        )
        logger.debug(
            f"We apply an energy mix of {emissions_per_kWh.kgs_per_kWh*1000:.0f}"
            + f" g.CO2eq/kWh for {geo.country_name}"
        )

        return emissions_per_kWh.kgs_per_kWh * energy.kWh  # kgs

    @staticmethod
    def _global_energy_mix_to_emissions_rate(energy_mix: Dict) -> EmissionsPerKWh:
        """
        Convert a mix of electricity sources into emissions per kWh.
        :param energy_mix: A dictionary that breaks down the electricity produced into
            energy sources, with a total value. Format will vary, but must have keys for "total_TWh"
        :return: an EmissionsPerKwh object representing the average emissions rate
            in Kgs.CO2 / kWh
        """
        # If we have the chance to have the carbon intensity for this country
        if energy_mix.get("carbon_intensity"):
            return EmissionsPerKWh.from_g_per_kWh(energy_mix.get("carbon_intensity"))

        # Else we compute it from the energy mix.
        # Read carbon_intensity from the json data file.
        carbon_intensity_per_source = (
            DataSource().get_carbon_intensity_per_source_data()
        )
        carbon_intensity = 0
        energy_sum = energy_mix["total_TWh"]
        energy_sum_computed = 0
        # Iterate through each source of energy in the country
        for energy_type, energy_per_year in energy_mix.items():
            if "_TWh" in energy_type:
                # Compute the carbon intensity ratio of this source for this country
                carbon_intensity_for_type = carbon_intensity_per_source.get(
                    energy_type[: -len("_Twh")]
                )
                if carbon_intensity_for_type:  # to ignore "total_TWh"
                    carbon_intensity += (
                        energy_per_year / energy_sum
                    ) * carbon_intensity_for_type
                    energy_sum_computed += energy_per_year

        # Sanity check
        if energy_sum_computed != energy_sum:
            logger.error(
                f"We find {energy_sum_computed} TWh instead of {energy_sum} TWh for {energy_mix.get('official_name_en')}, using world average."
            )
            return EmissionsPerKWh.from_g_per_kWh(
                carbon_intensity_per_source.get("world_average")
            )

        return EmissionsPerKWh.from_g_per_kWh(carbon_intensity)
