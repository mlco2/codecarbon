import threading
import time
from typing import Any, Dict, Tuple

import requests

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.external.logger import logger

_Key = Tuple[Tuple[Tuple[str, Any], ...], str]

URL: str = "https://api.electricitymaps.com/v3/carbon-intensity/latest"
ELECTRICITYMAPS_API_TIMEOUT: int = 30

# Grid carbon intensity is published hourly at best, while emissions are computed
# on every measurement tick, so the value is cached instead of refetched.
ELECTRICITYMAPS_CACHE_TTL: int = 60
# After a failure (bad token, network down), wait before retrying instead of
# issuing one doomed request per measurement tick.
ELECTRICITYMAPS_COOLDOWN: int = 60

# {(sorted query params, token): (monotonic fetch time, intensity in gCO2e/kWh)}
_cache: Dict[_Key, Tuple[float, float]] = {}
# {cache key: monotonic time until which requests are skipped}
# Keyed like the cache: one tracker's bad token must not block another's good one.
_cooldown: Dict[_Key, float] = {}
# The state above is read-modify-written from the measurement thread.
_lock = threading.Lock()


def reset_cache() -> None:
    """Drop the cached carbon intensities and any pending failure cooldown."""
    with _lock:
        _cache.clear()
        _cooldown.clear()


def _start_cooldown(key: _Key) -> None:
    with _lock:
        _cooldown[key] = time.monotonic() + ELECTRICITYMAPS_COOLDOWN


def get_carbon_intensity(
    geo: GeoMetadata, electricitymaps_api_token: str = ""
) -> float:
    """
    Retrieve the carbon intensity of the grid, in gCO2e/kWh, from the Electricity
    Maps API (formerly CO2 Signal) for the given geographic location.

    Raises:
        ElectricityMapsAPIError: the request failed, returned an error, or was
            skipped because a previous one failed (``...CooldownError``).
    """
    if geo.latitude:
        params: Dict[str, Any] = {"lat": geo.latitude, "lon": geo.longitude}
    else:
        params = {"countryCode": geo.country_2letter_iso_code}
    key = (tuple(sorted(params.items())), electricitymaps_api_token)
    with _lock:
        cached = _cache.get(key)
        cooldown_until = _cooldown.get(key, 0.0)
    if cached and time.monotonic() - cached[0] <= ELECTRICITYMAPS_CACHE_TTL:
        logger.debug(
            f"electricitymaps_api: using cached carbon intensity {cached[1]} gCO2e/kWh"
        )
        return cached[1]

    remaining = cooldown_until - time.monotonic()
    if remaining > 0:
        raise ElectricityMapsAPICooldownError(
            "Electricity Maps API is in cooldown after a previous failure, "
            f"retrying in {remaining:.0f} seconds"
        )

    try:
        resp = requests.get(
            URL,
            params=params,
            headers={"auth-token": electricitymaps_api_token},
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
        # API v3 response structure: carbonIntensity is at the root level
        carbon_intensity_g_per_kWh = resp.json().get("carbonIntensity")
        if carbon_intensity_g_per_kWh is None:
            raise ElectricityMapsAPIError("No carbonIntensity data in response")
    except Exception:
        _start_cooldown(key)
        raise

    with _lock:
        _cache[key] = (time.monotonic(), carbon_intensity_g_per_kWh)
        _cooldown.pop(key, None)
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
