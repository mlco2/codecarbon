import requests

from codecarbon.core.units import EmissionsPerKwh, Energy
from codecarbon.external.geography import GeoMetadata

URL = "https://api.co2signal.com/v1/latest"
CO2_SIGNAL_API_TOKEN = "47605efa6b1a6dc4"


def is_available():
    if CO2_SIGNAL_API_TOKEN:
        return True
    else:
        return False


def get_emissions(energy: Energy, geo: GeoMetadata):
    print("getting data from api")
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    print(params)
    data = requests.get(
        URL, params=params, headers={"auth-token": CO2_SIGNAL_API_TOKEN}
    )
    print(data.json())
    carbon_intensity_g_per_kWh = data.json()["data"]["carbonIntensity"]
    print(carbon_intensity_g_per_kWh)
    emissions_per_kwh: EmissionsPerKwh = EmissionsPerKwh.from_g_per_kwh(
        carbon_intensity_g_per_kWh
    )
    print(emissions_per_kwh)
    return emissions_per_kwh.kgs_per_kwh * energy.kwh
