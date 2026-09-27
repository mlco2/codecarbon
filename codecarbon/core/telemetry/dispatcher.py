"""Per-tracker telemetry dispatcher."""

from __future__ import annotations

import atexit
import os
import threading
import time
from pathlib import Path
from typing import Any

from codecarbon.core.telemetry.client import post_private
from codecarbon.core.telemetry.collect import build_payload
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

#: Total wall-clock budget for one send.
TELEMETRY_TIMEOUT_SECONDS = 2.0

#: How long interpreter exit waits for pending sends.
EXIT_JOIN_SECONDS = 1.0

THREAD_NAME = "codecarbon-telemetry"

#: Remembers, per machine, that the default-level notice was shown.
NOTICE_MARKER = Path.home() / ".codecarbon" / "telemetry_notice_shown"

TELEMETRY_NOTICE = (
    "CodeCarbon telemetry is on by default at level %r: once per process, "
    "stop() sends environment and hardware info (OS, Python and CodeCarbon "
    "versions, CPU/GPU model and count, RAM size, country/region, cloud "
    "provider); no code, data, file paths or coordinates. Opt out with "
    "`codecarbon telemetry set disabled` or "
    "CODECARBON_TELEMETRY_LEVEL=disabled. Details: "
    "https://docs.codecarbon.io/latest/how-to/telemetry/ "
    "This notice is shown once per machine."
)

_pending: set[threading.Thread] = set()

#: Telemetry describes the environment, which does not change within a
#: process, so only the first qualifying stop() sends it.
_sent_lock = threading.Lock()
_sent = False


def _reset_after_fork() -> None:
    """A forked child is its own process: let it send its own telemetry too.

    Also rebuilds the lock, since a lock inherited across ``fork()`` may be
    left held if another thread owned it at fork time.
    """
    global _sent, _sent_lock
    _sent = False
    _sent_lock = threading.Lock()
    _pending.clear()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_after_fork)


@atexit.register
def _join_pending() -> None:
    """Give in-flight sends a short, bounded chance to finish at exit."""
    deadline = time.monotonic() + EXIT_JOIN_SECONDS
    for thread in [t for t in list(_pending) if t.is_alive()]:
        thread.join(max(0.0, deadline - time.monotonic()))


class Telemetry:
    """Per-tracker telemetry dispatcher."""

    def __init__(self, settings: TelemetrySettings) -> None:
        self.settings = settings
        #: The last send thread, kept only so tests can join it.
        self._thread: threading.Thread | None = None

    def notice_once_if_implicit(self) -> None:
        """Explain the default tier once per machine when none was chosen."""
        if self.settings.is_explicit or self.settings.level == TelemetryLevel.disabled:
            return
        try:
            if NOTICE_MARKER.exists():
                return
            NOTICE_MARKER.parent.mkdir(parents=True, exist_ok=True)
            NOTICE_MARKER.touch()
        except OSError:
            pass  # read-only home: showing it again beats never showing it
        logger.warning(TELEMETRY_NOTICE, self.settings.level.value)

    def send_at_stop(self, tracker: Any, emissions: EmissionsData) -> None:
        """Send product telemetry on the first qualifying ``stop()`` of the process."""
        global _sent
        if self.settings.level == TelemetryLevel.disabled:
            return
        if emissions.duration is not None and emissions.duration < 1:
            logger.debug("Telemetry not sent: run shorter than 1 second.")
            return
        # Payload building (NVML, package lookups) and the network both happen
        # on this thread: stop() never waits on either. At exit it is joined for
        # at most EXIT_JOIN_SECONDS, then dropped. The whole claim-and-start
        # happens under the lock so two concurrent stop()s can't both start a
        # thread, and _sent is only set once a thread has actually started, so
        # stop() can never crash from telemetry and a failed start doesn't
        # permanently suppress every later send.
        with _sent_lock:
            if _sent:
                return
            try:
                thread = threading.Thread(
                    target=self._send,
                    args=(tracker, emissions),
                    name=THREAD_NAME,
                    daemon=True,
                )
                thread.start()
            except Exception:
                logger.debug("Telemetry thread failed to start.", exc_info=True)
                return
            self._thread = thread
            _pending.add(thread)
            _sent = True

    def _send(self, tracker: Any, emissions: EmissionsData) -> None:
        """Build and post the payload under one time budget."""
        deadline = time.monotonic() + TELEMETRY_TIMEOUT_SECONDS
        try:
            payload = build_payload(tracker, emissions, level=self.settings.level)
            post_private(self.settings, payload, deadline=deadline)
        except Exception:
            logger.debug("Telemetry send failed.", exc_info=True)
        finally:
            _pending.discard(threading.current_thread())
