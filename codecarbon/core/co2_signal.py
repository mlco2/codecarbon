from typing import Any, Dict

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata

URL: str = "https://api.co2signal.com/v1/latest"
CO2_SIGNAL_API_TIMEOUT: int = 30


def get_emissions(
    energy: Energy, geo: GeoMetadata, co2_signal_api_token: str = ""
) -> float:
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
