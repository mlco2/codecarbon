"""
Provides functionality to compute emissions for cloud & private infra based on impact & energy Usage package
https://github.com/mlco2/impact
https://github.com/responsibleproblemsolving/energy-usage
"""

import json
import logging
import pandas as pd
from typing import Dict, Optional

from co2_tracker.config import AppConfig
from co2_tracker.external.geography import GeoMetadata, CloudMetadata
from co2_tracker.units import CO2EmissionsPerKwh, Energy

logger = logging.getLogger(__name__)


def get_cloud_emissions(
    energy: Energy, cloud: CloudMetadata, config: AppConfig
) -> float:
    """
    Computes emissions for cloud infra
    :param energy: Mean power consumption of the process (kWh)
           cloud: Region of compute
           config: Location of data files
    :return: CO2 emissions in kg
    """

    df: pd.DataFrame = pd.read_csv(config.cloud_emissions_path)

    # TODO: deal with missing data

    emissions_per_kwh: CO2EmissionsPerKwh = CO2EmissionsPerKwh.from_g_per_kwh(
        df.loc[(df["provider"] == cloud.provider) & (df["region"] == cloud.region)][
            "impact"
        ].item()
    )

    return emissions_per_kwh.kgs_per_kwh * energy.kwh  # kgs


def get_cloud_country(cloud: CloudMetadata, config: AppConfig) -> str:
    df: pd.DataFrame = pd.read_csv(config.cloud_emissions_path)
    return df.loc[(df["provider"] == cloud.provider) & (df["region"] == cloud.region)][
        "country"
    ].item()


def get_private_infra_emissions(
    energy: Energy, geo: GeoMetadata, config: AppConfig
) -> float:
    """
    Computes emissions for private infra
    :param energy: Mean power consumption of the process (kWh)
           geo: Country and region metadata
           config: Location of data files
    :return: CO2 emissions in kg
    """
    compute_with_energy_mix: bool = geo.country != "United States" or (
        geo.country == "United States" and geo.region is None
    )

    return (
        _get_country_emissions_energy_mix(
            energy, geo, energy_mix_data_path=config.private_infra_energy_mix_path
        )
        if compute_with_energy_mix
        else _get_united_states_emissions(
            energy, geo, us_data_path=config.private_infra_us_path
        )
    )


def _get_united_states_emissions(
    energy: Energy, geo: GeoMetadata, us_data_path: str
) -> float:
    """
    Computes emissions for United States on private infra
    https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
    :param energy: Mean power consumption of the process (kWh)
           geo: Country and region metadata.
           us_data_path: Emission data for United States
    :return: CO2 emissions in kg
    """

    us_state: Optional[str] = geo.region

    with open(us_data_path) as f:
        us_state_emissions_data: Dict = json.load(f)

    if us_state not in us_state_emissions_data:
        # TODO: Deal with missing data, default to something
        raise Exception()

    emissions_per_kwh: CO2EmissionsPerKwh = CO2EmissionsPerKwh.from_lbs_per_mwh(
        us_state_emissions_data[us_state]
    )

    return emissions_per_kwh.kgs_per_kwh * energy.kwh


def _get_country_emissions_energy_mix(
    energy: Energy, geo: GeoMetadata, energy_mix_data_path: str
) -> float:
    """
    Computes emissions for International locations on private infra
    https://github.com/responsibleproblemsolving/energy-usage#calculating-co2-emissions
    :param energy: Mean power consumption of the process (kWh)
           geo: Country and region metadata.
           energy_mix_data_path: Energy mix data file path
    :return: CO2 emissions in kg
    """

    # source: https://github.com/responsibleproblemsolving/energy-usage#conversion-to-co2
    emissions_by_source: Dict[str, CO2EmissionsPerKwh] = {
        "coal": CO2EmissionsPerKwh.from_kgs_per_kwh(0.995725971),
        "petroleum": CO2EmissionsPerKwh.from_kgs_per_kwh(0.8166885263),
        "naturalGas": CO2EmissionsPerKwh.from_kgs_per_kwh(0.7438415916),
    }

    with open(energy_mix_data_path) as f:
        intl_energy_mix_data: Dict = json.load(f)

    if geo.country not in intl_energy_mix_data:
        # TODO: Deal with missing data, default to something
        raise Exception()

    country_data: Dict = intl_energy_mix_data[geo.country]

    emissions_percentage: Dict[str, float] = {
        emission: country_data[emission] / country_data["total"]
        for emission in country_data.keys() - {"total"}
    }

    #  Weighted sum of emissions by % of contributions
    # `emissions_percentage`: coal: 0.5, petroleum: 0.25, naturalGas: 0.25
    # `emission_value`: coal: 0.995725971, petroleum: 0.8166885263, naturalGas: 0.7438415916
    # `emissions_per_kwh`: (0.5 * 0.995725971) + (0.25 * 0.8166885263) * (0.25 * 0.7438415916)
    #  >> 0.5358309 kg/kwh
    emissions_per_kwh = CO2EmissionsPerKwh.from_kgs_per_kwh(
        sum(
            [
                emissions_percentage[source] * value.kgs_per_kwh  # % (0.x)  # kgs / kwh
                for source, value in emissions_by_source.items()
            ]
        )
    )

    return emissions_per_kwh.kgs_per_kwh * energy.kwh  # kgs
