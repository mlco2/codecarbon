import time

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata

# National Grid ESO Carbon Intensity API for Great Britain.
# Data source: https://carbonintensity.org.uk/ — published by National Grid ESO
# under the Open Government Licence v3.0. The API reports a single,
# national-level (Great-Britain-wide) carbon intensity figure; it does not
# provide regional or sub-national granularity.
URL: str = "https://api.carbonintensity.org.uk/intensity"

# Kept short deliberately: this call sits in the emissions fallback chain and
# must not stall a measurement if the API is slow or unreachable.
NATIONAL_GRID_ESO_API_TIMEOUT: int = 4

# Per-process cache of the last fetched carbon intensity, so a single
# long-running CodeCarbon session does not re-hit the API on every
# measurement. Keyed by nothing (single value) since this API only ever
# describes Great Britain as a whole; re-fetched once the entry expires.
_CACHE_TTL_SECONDS: int = 300
_cache: tuple[float, float] | None = None  # (carbon_intensity_g_per_kWh, fetched_at)


def _fetch_carbon_intensity_g_per_kWh() -> float:
    """Call the live API and return the current carbon intensity in gCO2/kWh."""
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
    carbon_intensity_g_per_kWh = (
        actual if actual is not None else intensity.get("forecast")
    )

    if carbon_intensity_g_per_kWh is None:
        raise NationalGridESOAPIError(
            "No actual or forecast carbon intensity in response"
        )

    return carbon_intensity_g_per_kWh


def _get_cached_carbon_intensity_g_per_kWh() -> float:
    """Return the cached intensity if still fresh, otherwise fetch and cache it."""
    global _cache
    now = time.monotonic()
    if _cache is not None:
        cached_value, fetched_at = _cache
        if (now - fetched_at) < _CACHE_TTL_SECONDS:
            return cached_value

    value = _fetch_carbon_intensity_g_per_kWh()
    _cache = (value, now)
    return value


def clear_cache() -> None:
    """Reset the cached carbon intensity value (mainly useful for tests)."""
    global _cache
    _cache = None


def get_emissions(energy: Energy, geo: GeoMetadata) -> float:
    """
    Calculate the CO2 emissions using the UK National Grid ESO Carbon Intensity API.

    This is an opt-in data source: callers must check ``is_supported`` and the
    caller-side opt-in flag before calling this. The value returned describes
    Great Britain as a whole; the API does not provide regional figures.

    Args:
        energy: Energy consumption in kWh.
        geo: Geographic metadata; must have country_iso_code == "GBR".

    Returns:
        CO2 emissions in kilograms.

    Raises:
        NationalGridESOAPIError: If the API request fails or returns unusable data.
    """
    carbon_intensity_g_per_kWh = _get_cached_carbon_intensity_g_per_kWh()

    emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kWh.kgs_per_kWh * energy.kWh


def is_supported(geo: GeoMetadata) -> bool:
    """Return True when the geo location is within Great Britain (GBR)."""
    return geo.country_iso_code == "GBR"


class NationalGridESOAPIError(Exception):
    pass
