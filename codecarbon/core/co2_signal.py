from typing import Any, Dict

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata

URL: str = "https://api.co2signal.com/v1/latest"
CO2_SIGNAL_API_TIMEOUT: int = 30


def get_emissions(
    energy: Energy, geo: GeoMetadata, co2_signal_api_token: str = ""
) -> float:
    """
    Calculate the CO2 emissions based on energy consumption and geographic location.

    This function retrieves the carbon intensity (in grams of CO2 per kWh) from the CO2
    Signal API based on the geographic location provided. It then calculates the total
    CO2 emissions for a given amount of energy consumption.

    Args:
        energy (Energy):
            An object representing the energy consumption in kilowatt-hours (kWh).
        geo (GeoMetadata):
            Geographic metadata, including either latitude/longitude
            or a country code.
        co2_signal_api_token (str, optional):
            The API token for authenticating with the CO2 Signal API (default is an empty string).

    Returns:
        float:
            The total CO2 emissions in kilograms based on the provided energy consumption and
            carbon intensity of the specified geographic location.

    Raises:
        CO2SignalAPIError:
            If the CO2 Signal API request fails or returns an error.
    """
    params: Dict[str, Any]
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    resp = requests.get(
        URL,
        params=params,
        headers={"auth-token": co2_signal_api_token},
        timeout=CO2_SIGNAL_API_TIMEOUT,
    )
    if resp.status_code != 200:
        message = resp.json().get("error") or resp.json().get("message")
        raise CO2SignalAPIError(message)
    carbon_intensity_g_per_kWh = resp.json()["data"]["carbonIntensity"]
    emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kWh.kgs_per_kWh * energy.kWh


class CO2SignalAPIError(Exception):
    pass
