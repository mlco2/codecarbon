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
        ]["countryName"].item()

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
            # TODO: Deal with missing data, default to something
            # TODO: return annual mean and log an error
            raise Exception()

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
            energy sources, with a total value. Format will vary, but must have keys for "fossil"
            and "total"
        :return: an EmissionsPerKwh object representing the average emissions rate
        """
        # TODO:
        # try/excep and return default value and log error
        # Des tests unitaires
        # Externaliser les valeur d'intensité carbone, avec la source pour chaque valeur.

        # If we have the chance to have the carbon intensity for this country
        if energy_mix.get("carbon_intensity"):
            return EmissionsPerKWh.from_kgs_per_kWh(
                energy_mix.get("carbon_intensity") / 1000
            )

        # Else we compute it from the energy mix.

        # source: https://www.epa.gov/egrid/data-explorer
        fossil_emissions_rate = EmissionsPerKWh.from_lbs_per_mWh(1401)
        fossil_mix_percentage = energy_mix["fossil"] / energy_mix["total"]

        # Source : https://www.world-nuclear.org/information-library/energy-and-the-environment/carbon-dioxide-emissions-from-electricity.aspx
        geothermal_emissions_rate = EmissionsPerKWh.from_g_per_kWh(38)
        geothermal_mix_percentage = energy_mix["geothermal"] / energy_mix["total"]

        # Source : http://www.world-nuclear.org/uploadedFiles/org/WNA/Publications/Working_Group_Reports/comparison_of_lifecycle.pdf
        hydroelectricity_emissions_rate = EmissionsPerKWh.from_g_per_kWh(26)
        hydroelectricity_mix_percentage = (
            energy_mix["hydroelectricity"] / energy_mix["total"]
        )

        nuclear_emissions_rate = EmissionsPerKWh.from_g_per_kWh(29)
        nuclear_mix_percentage = energy_mix["nuclear"] / energy_mix["total"]

        solar_emissions_rate = EmissionsPerKWh.from_g_per_kWh(48)
        solar_mix_percentage = energy_mix["solar"] / energy_mix["total"]

        wind_emissions_rate = EmissionsPerKWh.from_g_per_kWh(26)
        wind_mix_percentage = energy_mix["wind"] / energy_mix["total"]
        logger.debug("Code Carbon hypothesis for carbon intensity :")
        logger.debug(
            f"Fossil : {fossil_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        logger.debug(
            f"Geothermal : {geothermal_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        logger.debug(
            f"hydroelectricity : {hydroelectricity_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        logger.debug(
            f"nuclear : {nuclear_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        logger.debug(
            f"solar : {solar_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        logger.debug(
            f"wind : {wind_emissions_rate.kgs_per_kWh*1000:.0f} CO2.eq gs / kWh"
        )
        return EmissionsPerKWh.from_kgs_per_kWh(
            fossil_mix_percentage
            * fossil_emissions_rate.kgs_per_kWh  # % (0.x)  # kgs / kWh
            + geothermal_mix_percentage * geothermal_emissions_rate.kgs_per_kWh
            + hydroelectricity_mix_percentage
            * hydroelectricity_emissions_rate.kgs_per_kWh
            + nuclear_mix_percentage * nuclear_emissions_rate.kgs_per_kWh
            + solar_mix_percentage * solar_emissions_rate.kgs_per_kWh
            + wind_mix_percentage * wind_emissions_rate.kgs_per_kWh
        )
