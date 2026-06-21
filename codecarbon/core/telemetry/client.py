"""HTTP and API clients for product telemetry."""

from __future__ import annotations

import dataclasses

import requests

from codecarbon.core.api_client import ApiClient
from codecarbon.core.telemetry.schemas import TelemetryCreate
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData


def post_private(settings: TelemetrySettings, payload: dict) -> bool:
    """POST private telemetry to ``/telemetry``; return True on HTTP 201."""
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
            timeout=2,
        )
    except Exception:
        logger.error("Telemetry request failed.", exc_info=True)
        return False
    if response.status_code == 201:
        return True
    if response.status_code == 404:
        logger.warning(
            "Telemetry API not found at %s (HTTP 404); Tier 1 not recorded.",
            telemetry_url,
        )
    else:
        logger.error(
            "Telemetry API %s: %s",
            response.status_code,
            response.text,
        )
    return False


def post_public_summary(
    settings: TelemetrySettings,
    conf: dict,
    emissions: EmissionsData,
) -> bool:
    """Post public run summary via ``ApiClient`` (extensive tier only)."""
    try:
        api = ApiClient(
            endpoint_url=settings.api_url,
            experiment_id=settings.experiment_id,
            api_key=settings.api_key,
            conf=conf,
            create_run_automatically=True,
        )
        return bool(api.add_emission(dataclasses.asdict(emissions)))
    except Exception as error:
        logger.error(f"Public run summary failed (non-critical): {error}")
        return False
