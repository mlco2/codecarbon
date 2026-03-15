"""
The Carbon Tracker module. The following objects/decorators belong to the Public API
"""

from ._version import __version__  # noqa
from .emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from .core.telemetry import (
    TelemetryConfig,
    TelemetryTier,
    init_telemetry,
    set_telemetry,
)

__all__ = [
    "EmissionsTracker",
    "OfflineEmissionsTracker",
    "track_emissions",
    "TelemetryConfig",
    "TelemetryTier",
    "init_telemetry",
    "set_telemetry",
]
__app_name__ = "codecarbon"
