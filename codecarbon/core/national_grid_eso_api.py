"""
Deprecated location, kept so existing imports keep working.

Use ``codecarbon.core.carbon_intensity.NationalGridESOProvider`` instead.
"""

from codecarbon.core.carbon_intensity.national_grid_eso import (  # noqa: F401
    NATIONAL_GRID_ESO_API_TIMEOUT,
    NATIONAL_GRID_ESO_CACHE_TTL,
    NATIONAL_GRID_ESO_COOLDOWN,
    NATIONAL_GRID_ESO_MAX_COOLDOWN,
    URL,
    NationalGridESOAPICooldownError,
    NationalGridESOAPIError,
    NationalGridESOProvider,
)
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


def is_supported(geo: GeoMetadata) -> bool:
    return NationalGridESOProvider().is_supported(geo)


def clear_cache() -> None:
    NationalGridESOProvider.reset_cache()


def get_emissions(energy: Energy, geo: GeoMetadata) -> float:
    return NationalGridESOProvider().get_emissions(energy, geo)
