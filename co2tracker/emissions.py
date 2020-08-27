"""
Provides functionality to compute emissions for cloud & private infra based on impact & energy Usage package
https://github.com/mlco2/impact
https://github.com/responsibleproblemsolving/energy-usage
"""

import logging
import pandas as pd
from typing import Dict

from co2tracker.external.geography import GeoMetadata, CloudMetadata
from co2tracker.input import DataSource
from co2tracker.units import CO2EmissionsPerKwh, Energy

logger = logging.getLogger(__name__)


class Emissions:
    def __init__(self, data_source: DataSource):
        self._data_source = data_source

    def get_cloud_emissions(self, energy: Energy, cloud: CloudMetadata) -> float:
        """
        Computes emissions for cloud infra
        :param energy: Mean power consumption of the process (kWh)
        :param cloud: Region of compute
        :return: CO2 emissions in kg
        """

        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()

        # TODO: deal with missing data
        print(cloud.provider, cloud.region)
        print(
            df.loc[(df["provider"] == cloud.provider) & (df["region"] == cloud.region)]
        )
        emissions_per_kwh: CO2EmissionsPerKwh = CO2EmissionsPerKwh.from_g_per_kwh(
            df.loc[(df["provider"] == cloud.provider) & (df["region"] == cloud.region)][
                "impact"
            ].item()
        )

        return emissions_per_kwh.kgs_per_kwh * energy.kwh  # kgs

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
        compute_with_energy_mix: bool = geo.country_iso_code.upper() != "USA" or (
            geo.country_iso_code.upper() == "USA" and geo.region is None
        )

        if compute_with_energy_mix:
            return self.get_country_emissions(energy, geo)
        else:
            return self.get_region_emissions(energy, geo)

    def get_region_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for a country on private infra,
        given emissions per unit power consumed at a regional level
        https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata.
        :return: CO2 emissions in kg
        """

        country_emissions_data = self._data_source.get_country_emissions_data(
            geo.country_iso_code.lower()
        )

        if geo.region not in country_emissions_data:
            # TODO: Deal with missing data, default to something
            raise Exception(
                f"Region: {geo.region} not found for Country with ISO CODE : {geo.country_iso_code}"
            )

        emissions_per_kwh: CO2EmissionsPerKwh = CO2EmissionsPerKwh.from_lbs_per_mwh(
            country_emissions_data[geo.region]["emissions"]
        )

        return emissions_per_kwh.kgs_per_kwh * energy.kwh

    def get_country_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for a country on private infra,
        given emissions per unit power consumed at a country level
        https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: CO2 emissions in kg
        """

        # source: https://github.com/responsibleproblemsolving/energy-usage#conversion-to-co2
        emissions_by_source: Dict[str, CO2EmissionsPerKwh] = {
            "coal": CO2EmissionsPerKwh.from_kgs_per_kwh(0.995725971),
            "petroleum": CO2EmissionsPerKwh.from_kgs_per_kwh(0.8166885263),
            "naturalGas": CO2EmissionsPerKwh.from_kgs_per_kwh(0.7438415916),
        }

        energy_mix = self._data_source.get_global_energy_mix_data()

        if geo.country_iso_code not in energy_mix:
            # TODO: Deal with missing data, default to something
            raise Exception()

        country_energy_mix: Dict = energy_mix[geo.country_iso_code]

        emissions_percentage: Dict[str, float] = {}
        for energy_type in country_energy_mix.keys():
            if energy_type not in ["total", "isoCode", "countryName"]:
                emissions_percentage[energy_type] = (
                    country_energy_mix[energy_type] / country_energy_mix["total"]
                )

        #  Weighted sum of emissions by % of contributions
        # `emissions_percentage`: coal: 0.5, petroleum: 0.25, naturalGas: 0.25
        # `emission_value`: coal: 0.995725971, petroleum: 0.8166885263, naturalGas: 0.7438415916
        # `emissions_per_kwh`: (0.5 * 0.995725971) + (0.25 * 0.8166885263) * (0.25 * 0.7438415916)
        #  >> 0.5358309 kg/kwh
        emissions_per_kwh = CO2EmissionsPerKwh.from_kgs_per_kwh(
            sum(
                [
                    emissions_percentage[source]
                    * value.kgs_per_kwh  # % (0.x)  # kgs / kwh
                    for source, value in emissions_by_source.items()
                ]
            )
        )

        return emissions_per_kwh.kgs_per_kwh * energy.kwh  # kgs
