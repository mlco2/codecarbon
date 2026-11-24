"""
Deprecated location, kept so existing imports keep working.

Use ``codecarbon.core.carbon_intensity.ElectricityMapsProvider`` instead.
"""

from codecarbon.core.carbon_intensity.electricitymaps import (  # noqa: F401
    ELECTRICITYMAPS_API_TIMEOUT,
    ELECTRICITYMAPS_CACHE_TTL,
    ELECTRICITYMAPS_COOLDOWN,
    ELECTRICITYMAPS_MAX_COOLDOWN,
    URL,
    ElectricityMapsAPICooldownError,
    ElectricityMapsAPIError,
    ElectricityMapsProvider,
)
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


def reset_cache() -> None:
    ElectricityMapsProvider.reset_cache()


def get_carbon_intensity(
    geo: GeoMetadata, electricitymaps_api_token: str = ""
) -> float:
    return ElectricityMapsProvider(electricitymaps_api_token).get_carbon_intensity(geo)


def get_emissions(
    energy: Energy, geo: GeoMetadata, electricitymaps_api_token: str = ""
) -> float:
    return ElectricityMapsProvider(electricitymaps_api_token).get_emissions(energy, geo)
