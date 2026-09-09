import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata

URL: str = "https://api.carbonintensity.org.uk/intensity"
NATIONAL_GRID_ESO_API_TIMEOUT: int = 30


def get_emissions(energy: Energy, geo: GeoMetadata) -> float:
    """
    Calculate the CO2 emissions using the UK National Grid ESO Carbon Intensity API.

    Args:
        energy: Energy consumption in kWh.
        geo: Geographic metadata; must have country_iso_code == "GBR".

    Returns:
        CO2 emissions in kilograms.

    Raises:
        NationalGridESOAPIError: If the API request fails or returns unusable data.
    """
    resp = requests.get(URL, timeout=NATIONAL_GRID_ESO_API_TIMEOUT)
    if resp.status_code != 200:
        raise NationalGridESOAPIError(
            f"National Grid ESO API returned status {resp.status_code}"
        )

    try:
        intensity = resp.json()["data"][0]["intensity"]
    except (KeyError, IndexError, TypeError) as e:
        raise NationalGridESOAPIError(f"Unexpected response structure: {e}") from e

    # Prefer actual; fall back to forecast when actual has not been published yet.
    actual = intensity.get("actual")
    carbon_intensity_g_per_kWh = actual if actual is not None else intensity.get("forecast")

    if carbon_intensity_g_per_kWh is None:
        raise NationalGridESOAPIError(
            "No actual or forecast carbon intensity in response"
        )

    emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kWh.kgs_per_kWh * energy.kWh


def is_supported(geo: GeoMetadata) -> bool:
    """Return True when the geo location is within Great Britain (GBR)."""
    return geo.country_iso_code == "GBR"


class NationalGridESOAPIError(Exception):
    pass
