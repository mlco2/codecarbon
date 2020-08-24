"""
Provides functionality to compute emissions for cloud & private infra based on impact & energy Usage package
https://github.com/mlco2/impact
https://github.com/responsibleproblemsolving/energy-usage
"""

import logging
import pandas as pd
from typing import Dict, Optional

from co2_tracker.external.geography import GeoMetadata, CloudMetadata
from co2_tracker.input import DataSource
from co2_tracker.units import CO2EmissionsPerKwh, Energy

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

    def get_cloud_country(self, cloud: CloudMetadata) -> str:
        df: pd.DataFrame = self._data_source.get_cloud_emissions_data()
        return df.loc[
            (df["provider"] == cloud.provider) & (df["region"] == cloud.region)
        ]["country"].item()

    def get_private_infra_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for private infra
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata
        :return: CO2 emissions in kg
        """
        compute_with_energy_mix: bool = geo.country != "United States" or (
            geo.country == "United States" and geo.region is None
        )

        if compute_with_energy_mix:
            return self._get_country_emissions_energy_mix(energy, geo)
        else:
            return self._get_united_states_emissions(energy, geo)

    def _get_united_states_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """
        Computes emissions for United States on private infra
        https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
        :param energy: Mean power consumption of the process (kWh)
        :param geo: Country and region metadata.
        :return: CO2 emissions in kg
        """

        us_state: Optional[str] = geo.region

        us_state_emissions_data = self._data_source.get_usa_emissions_data()

        if us_state not in us_state_emissions_data:
            # TODO: Deal with missing data, default to something
            raise Exception()

        emissions_per_kwh: CO2EmissionsPerKwh = CO2EmissionsPerKwh.from_lbs_per_mwh(
            us_state_emissions_data[us_state]
        )

        return emissions_per_kwh.kgs_per_kwh * energy.kwh

    def _get_country_emissions_energy_mix(
        self, energy: Energy, geo: GeoMetadata
    ) -> float:
        """
        Computes emissions for International locations on private infra
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

        if geo.country not in energy_mix:
            # TODO: Deal with missing data, default to something
            raise Exception()

        country_energy_mix: Dict = energy_mix[geo.country]

        emissions_percentage: Dict[str, float] = {}
        for energy_type in country_energy_mix.keys():
            if energy_type not in ["total", "isoCode"]:
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
