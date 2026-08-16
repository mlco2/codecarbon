import threading
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
ELECTRICITYMAPS_CACHE_TTL: int = 60
# After a failure (bad token, network down), retry with an exponential cooldown
# instead of issuing one doomed request per measurement tick.
ELECTRICITYMAPS_COOLDOWN_MIN: int = 30
ELECTRICITYMAPS_COOLDOWN_MAX: int = 3600

# {cache key: (monotonic fetch time, carbon intensity in gCO2e/kWh)}
_cache: Dict[str, Tuple[float, float]] = {}
# {cache key: (monotonic time until which requests are skipped, cooldown length)}
# Keyed like the cache: one tracker's bad token must not block another's good one.
_cooldown: Dict[str, Tuple[float, float]] = {}
# Emissions are computed from a background measurement thread, so every
# read-modify-write of the state above is serialised. The lock is never held
# across the HTTP request.
_lock = threading.Lock()


def reset_cache() -> None:
    """Drop the cached carbon intensities and any pending failure cooldown."""
    with _lock:
        _cache.clear()
        _cooldown.clear()


def _cache_key(params: Dict[str, Any], electricitymaps_api_token: str) -> str:
    # The token is part of the key: two trackers in one process may use
    # different tokens, and must not share a cached value. Only an opaque,
    # process-local marker is kept, so the raw secret is never held in the
    # cache nor rendered in logs. builtin hash() is randomly seeded per
    # process and is not a password digest: it is used to tell tokens apart,
    # never to protect one.
    joined = ",".join(f"{key}={params[key]}" for key in sorted(params))
    return f"{joined},token={hash(electricitymaps_api_token):x}"


def _get_cached_carbon_intensity(key: str) -> Optional[float]:
    with _lock:
        cached = _cache.get(key)
    if cached is None:
        return None
    fetched_at, carbon_intensity_g_per_kWh = cached
    if time.monotonic() - fetched_at > ELECTRICITYMAPS_CACHE_TTL:
        return None
    return carbon_intensity_g_per_kWh


def _start_cooldown(key: str) -> None:
    with _lock:
        previous = _cooldown.get(key, (0.0, 0.0))[1]
        duration = min(
            ELECTRICITYMAPS_COOLDOWN_MAX,
            max(ELECTRICITYMAPS_COOLDOWN_MIN, previous * 2),
        )
        _cooldown[key] = (time.monotonic() + duration, duration)


def location_params(geo: GeoMetadata) -> Dict[str, Any]:
    """Build the Electricity Maps location query for a geography."""
    if geo.latitude:
        return {"lat": geo.latitude, "lon": geo.longitude}
    return {"countryCode": geo.country_2letter_iso_code}


def resolve_token() -> Optional[str]:
    """Read the Electricity Maps token from the hierarchical configuration.

    Falls back to the deprecated ``co2_signal_api_token`` name.
    """
    from codecarbon.core.config import get_hierarchical_config

    config = get_hierarchical_config()
    return config.get("electricitymaps_api_token") or config.get("co2_signal_api_token")


def request(url: str, params: Dict[str, Any], token: str) -> Any:
    """GET an Electricity Maps endpoint, sharing the failure cooldown.

    Every endpoint goes through here so that a failing location backs off once
    for the whole process instead of once per caller, and a usable response
    clears that location's cooldown.

    Raises:
        ElectricityMapsAPICooldownError: a previous request failed recently.
        ElectricityMapsAPIError: the API answered with an error.
    """
    key = _cache_key(params, token)
    with _lock:
        cooldown_until = _cooldown.get(key, (0.0, 0.0))[0]
    if time.monotonic() < cooldown_until:
        raise ElectricityMapsAPICooldownError(
            "Electricity Maps API is in cooldown after a previous failure, "
            f"retrying in {cooldown_until - time.monotonic():.0f} seconds"
        )

    try:
        resp = requests.get(
            url,
            params=params,
            headers={"auth-token": token},
            timeout=ELECTRICITYMAPS_API_TIMEOUT,
        )
        if resp.status_code != 200:
            try:
                body = resp.json()
            except ValueError:
                body = {}
            raise ElectricityMapsAPIError(
                body.get("error") or body.get("message") or resp.text
            )
        data = resp.json()
    except Exception:
        _start_cooldown(key)
        raise

    with _lock:
        _cooldown.pop(key, None)
    return data


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
    params = location_params(geo)
    key = _cache_key(params, electricitymaps_api_token)
    cached_carbon_intensity = _get_cached_carbon_intensity(key)
    if cached_carbon_intensity is not None:
        logger.debug(
            "electricitymaps_api: using cached carbon intensity "
            f"{cached_carbon_intensity} gCO2e/kWh for {key}"
        )
        return cached_carbon_intensity

    response_data = request(URL, params, electricitymaps_api_token)
    # API v3 response structure: carbonIntensity is at the root level
    carbon_intensity_g_per_kWh = response_data.get("carbonIntensity")
    if carbon_intensity_g_per_kWh is None:
        _start_cooldown(key)
        raise ElectricityMapsAPIError("No carbonIntensity data in response")

    with _lock:
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
