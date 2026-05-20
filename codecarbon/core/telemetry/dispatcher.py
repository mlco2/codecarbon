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
    "CodeCarbon telemetry_level was not set explicitly; using default %r. "
    "Tier 1 private telemetry (per run at stop) will be sent. Set telemetry_level "
    "in .codecarbon.config, set CODECARBON_TELEMETRY_LEVEL, pass telemetry_level=... "
    "to EmissionsTracker / OfflineEmissionsTracker, or run "
    "codecarbon telemetry set <level>."
)


class Telemetry:
    """Per-tracker telemetry dispatcher."""

    _default_warning_shown: ClassVar[bool] = False

    def __init__(self, settings: TelemetrySettings) -> None:
        self.settings = settings

    @classmethod
    def from_tracker(cls, tracker: Any) -> Telemetry:
        """Build a dispatcher from tracker config state.

        Args:
            tracker: Active emissions tracker with ``_config_file_conf``,
                ``_external_conf``, and optional ``_telemetry_override``.

        Returns:
            Configured ``Telemetry`` instance.
        """
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
        """Send product telemetry for the resolved tier at tracker ``stop()``.

        Tier 1 (``minimal``): private ``POST /telemetry`` only.
        Tier 2 (``extensive``): Tier 1 plus public run summary.

        Args:
            tracker: Active emissions tracker instance.
            emissions: Total emissions from ``_prepare_emissions_data()``.
        """
        if self.settings.level == TelemetryLevel.disabled:
            return
        if emissions.duration is not None and emissions.duration < 1:
            logger.debug("Telemetry not sent: run shorter than 1 second.")
            return
        ctx = TelemetryContext.from_tracker(tracker, emissions)
        payload = build_payload(ctx, level=self.settings.level)
        try:
            post_private(self.settings, payload)
        except Exception as error:
            logger.error(f"Private telemetry failed (non-critical): {error}")
        if self.settings.level == TelemetryLevel.extensive:
            try:
                post_public_summary(
                    self.settings,
                    getattr(tracker, "_conf", {}),
                    emissions,
                )
            except Exception as error:
                logger.error(f"Public run summary failed (non-critical): {error}")
