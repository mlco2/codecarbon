"""Per-tracker telemetry dispatcher."""

from __future__ import annotations

from typing import Any, ClassVar

from codecarbon.core.telemetry.client import post_private, post_public_summary
from codecarbon.core.telemetry.collect import TelemetryContext, build_payload
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

TELEMETRY_NOT_CONFIGURED_MESSAGE = (
    "telemetry_level not set explicitly; default %r. Minimal telemetry sends on each "
    "stop. Set telemetry_level in .codecarbon.config, CODECARBON_TELEMETRY_LEVEL, "
    "EmissionsTracker(telemetry_level=...), or: codecarbon telemetry set <level>."
)


class Telemetry:
    """Per-tracker telemetry dispatcher."""

    _default_warning_shown: ClassVar[bool] = False

    def __init__(self, settings: TelemetrySettings) -> None:
        self.settings = settings

    @classmethod
    def from_tracker(cls, tracker: Any) -> Telemetry:
        """Build a dispatcher from tracker config state."""
        return cls(
            TelemetrySettings.resolve(
                config_file_conf=tracker._config_file_conf,
                external_conf=tracker._external_conf,
                override=getattr(tracker, "_telemetry_override", None),
            )
        )

    def warn_if_implicit(self) -> None:
        """Log a one-time warning when telemetry tier was not set explicitly."""
        if self.settings.is_explicit or Telemetry._default_warning_shown:
            return
        logger.warning(
            TELEMETRY_NOT_CONFIGURED_MESSAGE,
            self.settings.level.value,
        )
        Telemetry._default_warning_shown = True

    def send_at_stop(self, tracker: Any, emissions: EmissionsData) -> None:
        """Send product telemetry at tracker ``stop()`` for the resolved tier."""
        if self.settings.level == TelemetryLevel.disabled:
            return
        if emissions.duration is not None and emissions.duration < 1:
            logger.debug("Telemetry not sent: run shorter than 1 second.")
            return
        ctx = TelemetryContext.from_tracker(tracker, emissions)
        payload = build_payload(ctx, level=self.settings.level)
        post_private(self.settings, payload)
        if self.settings.level == TelemetryLevel.extensive:
            post_public_summary(
                self.settings,
                getattr(tracker, "_conf", {}),
                emissions,
            )
