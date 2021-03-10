import requests

from codecarbon.core.units import EmissionsPerKwh, Energy
from codecarbon.external.geography import GeoMetadata

URL = "https://api.co2signal.com/v1/latest"
CO2_SIGNAL_API_TOKEN = None


def is_available():
    if CO2_SIGNAL_API_TOKEN:
        return True
    else:
        return False


def get_emissions(energy: Energy, geo: GeoMetadata, timeout=60):
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    resp = requests.get(
        URL,
        params=params,
        headers={"auth-token": CO2_SIGNAL_API_TOKEN},
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
