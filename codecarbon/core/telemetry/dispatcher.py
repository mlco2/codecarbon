"""Per-tracker telemetry dispatcher."""

from __future__ import annotations

import threading
import time
from typing import Any, ClassVar

from codecarbon.core.telemetry.client import post_private, post_public_summary
from codecarbon.core.telemetry.collect import build_payload
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

#: Total wall-clock budget for one ``send_at_stop``, shared by every request it
#: makes, so the extensive tier cannot cost more than the minimal one.
TELEMETRY_TIMEOUT_SECONDS = 2.0

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
        #: The last send thread, kept only so tests can join it.
        self._thread: threading.Thread | None = None

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
        if not self.settings.api_key:
            logger.debug("Telemetry not sent: no telemetry API key configured.")
            return
        if emissions.duration is not None and emissions.duration < 1:
            logger.debug("Telemetry not sent: run shorter than 1 second.")
            return
        payload = build_payload(tracker, emissions, level=self.settings.level)
        # Fire and forget on a daemon thread: stop() must never block on the
        # network. If the process exits before the send completes the telemetry
        # is simply lost, which is the right tradeoff for telemetry.
        self._thread = threading.Thread(
            target=self._send,
            args=(payload, getattr(tracker, "_conf", {}), emissions),
            name="codecarbon-telemetry",
            daemon=True,
        )
        self._thread.start()

    def _send(self, payload: dict, conf: dict, emissions: EmissionsData) -> None:
        """Run every request of one send under a single shared time budget."""
        deadline = time.monotonic() + TELEMETRY_TIMEOUT_SECONDS
        try:
            post_private(self.settings, payload, deadline=deadline)
            if self.settings.level == TelemetryLevel.extensive:
                post_public_summary(self.settings, conf, emissions, deadline=deadline)
        except Exception:
            logger.debug("Telemetry send failed.", exc_info=True)
