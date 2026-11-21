"""
Live grid carbon intensity providers.

Each module of this package implements one ``CarbonIntensityProvider`` (see
``base.py``). ``build_providers`` turns the tracker's resolved configuration
into the providers to try, in priority order, before CodeCarbon's static data.
"""

from typing import Any, List, Mapping, Type

from codecarbon.core.carbon_intensity.base import (
    CarbonIntensityCooldownError,
    CarbonIntensityError,
    CarbonIntensityProvider,
)
from codecarbon.core.carbon_intensity.electricitymaps import ElectricityMapsProvider
from codecarbon.core.carbon_intensity.national_grid_eso import NationalGridESOProvider

# Priority order: the first provider that covers the location and answers wins.
PROVIDER_CLASSES: List[Type[CarbonIntensityProvider]] = [
    ElectricityMapsProvider,
    NationalGridESOProvider,
]


def build_providers(conf: Mapping[str, Any]) -> List[CarbonIntensityProvider]:
    """
    Return the providers enabled by ``conf``, in priority order.

    ``conf`` is the tracker's resolved configuration; each provider reads only
    its own keys from it.
    """
    providers = (cls.from_config(conf) for cls in PROVIDER_CLASSES)
    return [p for p in providers if p is not None]


__all__ = [
    "PROVIDER_CLASSES",
    "CarbonIntensityCooldownError",
    "CarbonIntensityError",
    "CarbonIntensityProvider",
    "ElectricityMapsProvider",
    "NationalGridESOProvider",
    "build_providers",
]
