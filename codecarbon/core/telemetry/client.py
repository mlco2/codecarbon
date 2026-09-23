"""HTTP and API clients for product telemetry."""

from __future__ import annotations

import dataclasses
import time
from typing import Optional

import requests

from codecarbon.core.api_client import ApiClient
from codecarbon.core.telemetry.schemas import TelemetryCreate
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

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
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["x-api-token"] = settings.api_key
    body = TelemetryCreate(**payload).model_dump(mode="json", exclude_none=True)
    telemetry_url = f"{settings.api_url.rstrip('/')}/telemetry"
    try:
        response = requests.post(
            url=telemetry_url,
            json=body,
            headers=headers,
            timeout=timeout,
        )
    except Exception:
        logger.debug("Telemetry request failed.", exc_info=True)
        return False
    if response.status_code == 201:
        return True
    if response.status_code == 404:
        logger.warning(
            "Telemetry API not found at %s (HTTP 404); Tier 1 not recorded.",
            telemetry_url,
        )
    else:
        logger.debug(
            "Telemetry API %s: %s",
            response.status_code,
            response.text,
        )
    return False


def post_public_summary(
    settings: TelemetrySettings,
    conf: dict,
    emissions: EmissionsData,
    deadline: Optional[float] = None,
) -> bool:
    if remaining_time(deadline) <= 0:
        logger.debug("Public run summary not sent: time budget exhausted.")
        return False
    try:
        api = ApiClient(
            endpoint_url=settings.api_url,
            experiment_id=settings.experiment_id,
            api_key=settings.api_key,
            conf=conf,
            create_run_automatically=True,
            deadline=deadline,
        )
        return bool(api.add_emission(dataclasses.asdict(emissions)))
    except Exception as error:
        logger.debug(f"Public run summary failed (non-critical): {error}")
        return False
