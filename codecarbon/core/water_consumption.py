"""
Provides functionality to compute water consumption for cloud & private infra
"""

from typing import Dict, Optional

import pandas as pd

from codecarbon.core.units import Energy, WaterPerKWh
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.external.logger import logger
from codecarbon.input import DataSource


class WaterConsumption:
    def __init__(
        self,
        data_source: DataSource,
        electricitymaps_api_token: Optional[str] = None,
    ):
        self._data_source = data_source
        self._electricitymaps_api_token = electricitymaps_api_token

    def get_cloud_water_consumption(
        self, energy: Energy, cloud: CloudMetadata, geo: GeoMetadata = None
    ) -> float:
        """
        Computes water consumption for cloud infra
        :param energy: Mean power consumption of the process (kWh)
        :param cloud: Region of compute
        :param geo: Instance of GeoMetadata to fallback if we don't find cloud water usage intensity
        :return: water consumption in L
        """
        # TODO consume scaleway api
        logger.warning(
            f"Cloud water usage effectiveness for provider '{cloud.provider}' and region '{cloud.region}' not found, using country value instead."
        )
        logger.warning(
            "AWS and Azure do not provide any water usage effectiveness data. Only Scaleway does it."
        )
        if geo:
            water_consumption = self.get_private_infra_water_consumption(
                energy, geo
            )  # float: l water_eq
        else:
            water_consumption_per_source = (
                DataSource().get_water_consumption_per_source_data()
            )
            water_consumption = (
                WaterPerKWh.from_gal_us_per_kWh(
                    water_consumption_per_source.get("world_average")
                ).l_per_kWh
                * energy.kWh
            )  # l

        return water_consumption

    def get_cloud_country_name(self, cloud: CloudMetadata) -> str:
        """
        Returns the Country Name where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        flags = (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        selected = df.loc[flags]
        if not len(selected):
            raise ValueError(
                "Unable to find country name for "
                f"cloud_provider={cloud.provider}, "
                f"cloud_region={cloud.region}"
            )
        return selected["country_name"].item()

    def get_cloud_country_iso_code(self, cloud: CloudMetadata) -> str:
        """
        Returns the Country ISO Code where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        flags = (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        selected = df.loc[flags]
        if not len(selected):
            raise ValueError(
                "Unable to find country ISO Code for "
                f"cloud_provider={cloud.provider}, "
                f"cloud_region={cloud.region}"
            )
        return selected["countryIsoCode"].item()

    def get_cloud_geo_region(self, cloud: CloudMetadata) -> str:
        """
        Returns the State/City where the cloud region is located
        """
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        flags = (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        selected = df.loc[flags]
        if not len(selected):
            raise ValueError(
                "Unable to find State/City name for "
                f"cloud_provider={cloud.provider}, "
                f"cloud_region={cloud.region}"
            )

        state = selected["state"].item()
        if state is not None:
            return state
        city = selected["city"].item()
        return city

    def get_private_infra_water_consumption(
        self, energy: Energy, geo: GeoMetadata
    ) -> float:
        """
        Computes water consumption for private infra
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: water consumption in L
        """

        compute_with_regional_data: bool = (geo.region is not None) and (
            geo.country_iso_code.upper() in ["USA", "CAN"]
        )

        if compute_with_regional_data:
            try:
                return self.get_region_water_consumption(energy, geo)
            except Exception as e:
                logger.error(e, exc_info=True)
                logger.warning(
                    "Regional water consumption retrieval failed."
                    + " Falling back on country water consumption."
                )
        return self.get_country_water_consumption(energy, geo)

    def get_region_water_consumption(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes water consumption for a region on private infra.
        Given an quantity of power consumed, use regional data
         on consumption per unit power consumed or the mix of energy sources.
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata.
        :return: water consumption in L
        """

        country_energy_mix_data = self._data_source.get_country_energy_mix_data(
            geo.country_iso_code.lower()
        )
        region_energy_mix_data = country_energy_mix_data[geo.region]
        water_consumption_per_kWh = self._region_energy_mix_to_water_consumption_rate(
            region_energy_mix_data
        )

        return water_consumption_per_kWh.l_per_kWh * energy.kWh  # L

    def get_country_water_consumption(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes water consumption for a country on private infra,
        given a quantity of power consumed by
        using data for the mix of energy sources of that country.
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: water consumption in l
        """
        energy_mix = self._data_source.get_global_energy_mix_data()

        if geo.country_iso_code not in energy_mix:
            logger.warning(
                f"We do not have data for {geo.country_iso_code}, using world average."
            )
            water_consumption_per_source_data = (
                DataSource().get_water_consumption_per_source_data()
            )
            return (
                WaterPerKWh.from_gal_us_per_MWh(
                    water_consumption_per_source_data.get("world_average")
                ).l_per_kWh
                * energy.kWh
            )  # l

        country_energy_mix: Dict = energy_mix[geo.country_iso_code]
        water_consumption_per_kWh = self._global_energy_mix_to_water_consumption_rate(
            country_energy_mix
        )
        logger.debug(
            f"We apply an energy mix of {water_consumption_per_kWh.l_per_kWh * 1000:.0f}"
            + f" ml.Water.eq/kWh for {geo.country_name}"
        )

        return water_consumption_per_kWh.l_per_kWh * energy.kWh  # L

    @staticmethod
    def _global_energy_mix_to_water_consumption_rate(energy_mix: Dict) -> WaterPerKWh:
        """
        Convert a mix of electricity sources into water consumption per kWh.
        :param energy_mix: A dictionary that breaks down the electricity produced into
            energy sources, with a total value. Format will vary, but must have keys for "total_TWh"
        :return: an WaterPerKWh object representing the average water consumption rate
            in L.water / kWh
        """
        # We compute it from the energy mix.
        # Read water_consumption from the json data file.
        water_consumption_per_source = (
            DataSource().get_water_consumption_per_source_data()
        )
        water_consumption = 0
        energy_sum = energy_mix["total_TWh"]
        energy_sum_computed = 0
        # Iterate through each source of energy in the country
        for energy_type, energy_per_year in energy_mix.items():
            if "_TWh" in energy_type:
                # Compute the water consumption ratio of this source for this country
                water_consumption_for_type = water_consumption_per_source.get(
                    energy_type[: -len("_TWh")]
                )
                if water_consumption_for_type:  # to ignore "total_TWh"
                    water_consumption += (
                        energy_per_year / energy_sum
                    ) * water_consumption_for_type
                    energy_sum_computed += energy_per_year

        # Sanity check
        if energy_sum_computed != energy_sum:
            logger.error(
                f"We find {energy_sum_computed} TWh instead of {energy_sum} TWh for {energy_mix.get('country_name')}, using world average."
            )
            return WaterPerKWh.from_gal_us_per_MWh(
                water_consumption_per_source.get("world_average")
            )

        return WaterPerKWh.from_g_per_kWh(water_consumption)

    @staticmethod
    def _region_energy_mix_to_water_consumption_rate(energy_mix: Dict) -> WaterPerKWh:
        """
        Convert a mix of energy sources into water consumption per kWh
        :param energy_mix: A dictionary that breaks down the energy produced into
            sources, with a total value. Format will vary, but must have keys for "coal"
            "petroleum" and "naturalGas" and "total"
        :return: an WaterPerKWh object representing the average water consumption rate
        """
        water_consumption_per_source = (
            DataSource().get_water_consumption_per_source_data()
        )
        # TODO
        consumption_by_source: Dict[str, WaterPerKWh] = {
            "coal": WaterPerKWh.from_gal_us_per_MWh(
                water_consumption_per_source.get("coal")
            ),
            "petroleum": WaterPerKWh.from_gal_us_per_MWh(
                water_consumption_per_source.get("coal")
            ),  # estimation made on coal consumption
            "naturalGas": WaterPerKWh.from_gal_us_per_MWh(
                water_consumption_per_source.get("natural_gas")
            ),
        }
        consumption_percentage: Dict[str, float] = {}
        for energy_type in energy_mix.keys():
            if energy_type not in ["total", "isoCode", "country_name"]:
                consumption_percentage[energy_type] = (
                    energy_mix[energy_type] / energy_mix["total"]
                )
        #  Weighted sum of water consumption by % of contributions
        # `consumption_percentage`: coal: 0.5, petroleum: 0.25, naturalGas: 0.25
        # `consumption_value`: coal: 0.995725971, petroleum: 0.8166885263, naturalGas: 0.7438415916 # noqa: E501
        # `consumption_per_kWh`: (0.5 * 0.995725971) + (0.25 * 0.8166885263) * (0.25 * 0.7438415916) # noqa: E501
        #  >> 0.5358309 kg/kWh
        consumption_per_kWh = WaterPerKWh.from_l_per_kWh(
            sum(
                [
                    consumption_percentage[source]
                    * value.l_per_kWh  # % (0.x)  # l / kWh
                    for source, value in consumption_by_source.items()
                ]
            )
        )

        return consumption_per_kWh
