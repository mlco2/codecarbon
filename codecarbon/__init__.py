"""
The Carbon Tracker module. The following objects/decorators belong to the Public API
"""

from ._version import __version__  # noqa
from .emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from .output_methods.openllmetry import (
    enable_openllmetry,
    disable_openllmetry,
    is_openllmetry_enabled,
)

__all__ = [
    "EmissionsTracker",
    "OfflineEmissionsTracker",
    "track_emissions",
    "enable_openllmetry",
    "disable_openllmetry",
    "is_openllmetry_enabled",
]
__app_name__ = "codecarbon"
