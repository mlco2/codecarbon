"""HTTP client for product telemetry."""

from __future__ import annotations

import time
from typing import Optional

import requests

from codecarbon.core.telemetry.schemas import TelemetryCreate
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger

DEFAULT_TIMEOUT = 2.0


def remaining_time(deadline: Optional[float]) -> float:
    """Seconds left before ``deadline`` (a ``time.monotonic()`` value)."""
    if deadline is None:
        return DEFAULT_TIMEOUT
    return max(0.0, deadline - time.monotonic())


def post_private(
    settings: TelemetrySettings, payload: dict, deadline: Optional[float] = None
) -> bool:
    timeout = remaining_time(deadline)
    if timeout <= 0:
        logger.debug("Telemetry not sent: time budget exhausted.")
        return False
    body = TelemetryCreate(**payload).model_dump(mode="json", exclude_none=True)
    telemetry_url = f"{settings.api_url.rstrip('/')}/telemetry"
    try:
        response = requests.post(url=telemetry_url, json=body, timeout=timeout)
    except Exception:
        logger.debug("Telemetry request failed.", exc_info=True)
        return False
    if response.status_code == 201:
        return True
    # Best effort: never bother the user about a telemetry endpoint.
    logger.debug(
        "Telemetry API %s returned %s: %s",
        telemetry_url,
        response.status_code,
        response.text,
    )
    return False
