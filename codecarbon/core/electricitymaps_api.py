import time
from typing import Any, Dict, Optional, Tuple

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.external.logger import logger

URL: str = "https://api.electricitymaps.com/v3/carbon-intensity/latest"
ELECTRICITYMAPS_API_TIMEOUT: int = 30

# Grid carbon intensity is published hourly at best, while emissions are computed
# on every measurement tick, so the value is cached instead of refetched.
ELECTRICITYMAPS_CACHE_TTL: int = 300
# After a failure (bad token, network down), retry with an exponential cooldown
# instead of issuing one doomed request per measurement tick.
ELECTRICITYMAPS_COOLDOWN_MIN: int = 30
ELECTRICITYMAPS_COOLDOWN_MAX: int = 3600

# {cache key: (monotonic fetch time, carbon intensity in gCO2e/kWh)}
_cache: Dict[str, Tuple[float, float]] = {}
_cooldown_until: float = 0.0
_cooldown_duration: float = 0.0


def reset_cache() -> None:
    """Drop the cached carbon intensities and any pending failure cooldown."""
    global _cooldown_until, _cooldown_duration
    _cache.clear()
    _cooldown_until = 0.0
    _cooldown_duration = 0.0


def _cache_key(params: Dict[str, Any], electricitymaps_api_token: str) -> str:
    # The token is part of the key: two trackers in one process may use
    # different tokens, and must not share a cached value.
    joined = ",".join(f"{key}={params[key]}" for key in sorted(params))
    return f"{joined},token={electricitymaps_api_token}"


def _get_cached_carbon_intensity(key: str) -> Optional[float]:
    cached = _cache.get(key)
    if cached is None:
        return None
    fetched_at, carbon_intensity_g_per_kWh = cached
    if time.monotonic() - fetched_at > ELECTRICITYMAPS_CACHE_TTL:
        return None
    return carbon_intensity_g_per_kWh


def _start_cooldown() -> None:
    global _cooldown_until, _cooldown_duration
    _cooldown_duration = min(
        ELECTRICITYMAPS_COOLDOWN_MAX,
        max(ELECTRICITYMAPS_COOLDOWN_MIN, _cooldown_duration * 2),
    )
    _cooldown_until = time.monotonic() + _cooldown_duration


def get_carbon_intensity(
    geo: GeoMetadata, electricitymaps_api_token: str = ""
) -> float:
    """
    Retrieve the carbon intensity of the grid, in gCO2e/kWh, from the Electricity
    Maps API (formerly CO2 Signal) for the given geographic location.

    Values are cached for ``ELECTRICITYMAPS_CACHE_TTL`` seconds, and failures put
    the API in an exponential cooldown during which no request is issued.

    Args:
        geo (GeoMetadata):
            Geographic metadata, including either latitude/longitude
            or a country code.
        electricitymaps_api_token (str, optional):
            The API token for authenticating with the Electricity Maps API
            (default is an empty string).

    Returns:
        float:
            The carbon intensity of the grid, in grams of CO2eq per kWh.

    Raises:
        ElectricityMapsAPIError:
            If the Electricity Maps API request fails, returns an error, or is
            currently in a failure cooldown.
    """
    global _cooldown_duration
    params: Dict[str, Any]
    if geo.latitude:
        params = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}

    key = _cache_key(params, electricitymaps_api_token)
    cached_carbon_intensity = _get_cached_carbon_intensity(key)
    if cached_carbon_intensity is not None:
        logger.debug(
            "electricitymaps_api: using cached carbon intensity "
            f"{cached_carbon_intensity} gCO2e/kWh for {key}"
        )
        return cached_carbon_intensity

    if time.monotonic() < _cooldown_until:
        raise ElectricityMapsAPICooldownError(
            "Electricity Maps API is in cooldown after a previous failure, "
            f"retrying in {_cooldown_until - time.monotonic():.0f} seconds"
        )

    try:
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
    except Exception:
        _start_cooldown()
        raise

    _cooldown_duration = 0.0
    _cache[key] = (time.monotonic(), carbon_intensity_g_per_kWh)
    return carbon_intensity_g_per_kWh


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
    carbon_intensity_g_per_kWh = get_carbon_intensity(geo, electricitymaps_api_token)
    emissions_per_kWh: EmissionsPerKWh = EmissionsPerKWh.from_g_per_kWh(
        carbon_intensity_g_per_kWh
    )
    return emissions_per_kWh.kgs_per_kWh * energy.kWh


class ElectricityMapsAPIError(Exception):
    pass


class ElectricityMapsAPICooldownError(ElectricityMapsAPIError):
    """Raised when a request is skipped because a previous one failed."""
