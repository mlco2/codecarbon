"""
The Carbon Tracker module. The following objects/decorators belong to the Public API
"""

from ._version import __version__
from .emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)

__all__ = ["EmissionsTracker", "OfflineEmissionsTracker", "track_emissions"]

__version__ = __version__
