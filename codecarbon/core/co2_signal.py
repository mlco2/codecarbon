import requests

from codecarbon.core.units import EmissionsPerKwh, Energy
from codecarbon.external.geography import GeoMetadata

URL = "https://api.co2signal.com/v1/latest"


def get_emissions(
    energy: Energy, geo: GeoMetadata, timeout=60, co2_signal_api_token: str = ""
):
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    resp = requests.get(
        URL,
        params=params,
        headers={"auth-token": co2_signal_api_token},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise CO2SignalAPIError(resp.json()["error"])
    carbon_intensity_g_per_kWh = resp.json()["data"]["carbonIntensity"]
    emissions_per_kwh: EmissionsPerKwh = EmissionsPerKwh.from_g_per_kwh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kwh.kgs_per_kwh * energy.kwh


class CO2SignalAPIError(Exception):
    pass
