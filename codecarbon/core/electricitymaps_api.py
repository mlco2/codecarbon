from typing import Any, Dict

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata

URL: str = "https://api.electricitymaps.com/v3/carbon-intensity/latest"
ELECTRICITYMAPS_API_TIMEOUT: int = 30


def get_emissions(
    energy: Energy, geo: GeoMetadata, electricitymaps_api_token: str = ""
) -> float:
    """
    Calculate the CO2 emissions based on energy consumption and geographic location.

    This function retrieves the carbon intensity (in grams of CO2 per kWh) from the
    Electricity Maps API (formerly CO2 Signal) based on the geographic location provided.
    It then calculates the total CO2 emissions for a given amount of energy consumption.

    Args:
        energy (Energy):
            An object representing the energy consumption in kilowatt-hours (kWh).
        geo (GeoMetadata):
            Geographic metadata, including either latitude/longitude
            or a country code.
        electricitymaps_api_token (str, optional):
            The API token for authenticating with the Electricity Maps API (default is an empty string).

    Returns:
        float:
            The total CO2 emissions in kilograms based on the provided energy consumption and
            carbon intensity of the specified geographic location.

    Raises:
        ElectricityMapsAPIError:
            If the Electricity Maps API request fails or returns an error.
    """
    params: Dict[str, Any]
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    resp = requests.get(
        URL,
        params=params,
        headers={"auth-token": electricitymaps_api_token},
        timeout=ELECTRICITYMAPS_API_TIMEOUT,
    )
    if resp.status_code != 200:
        message = resp.json().get("error") or resp.json().get("message")
        raise ElectricityMapsAPIError(message)

    # API v3 response structure: carbonIntensity is at the root level
    response_data = resp.json()
    carbon_intensity_g_per_kWh = response_data.get("carbonIntensity")

    if carbon_intensity_g_per_kWh is None:
        raise ElectricityMapsAPIError("No carbonIntensity data in response")

    emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kWh.kgs_per_kWh * energy.kWh


class ElectricityMapsAPIError(Exception):
    pass
