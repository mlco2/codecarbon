"""Tracker-facing telemetry helpers built on the shared TelemetryClient."""

import os
from datetime import datetime, timezone
from typing import Any

from codecarbon.core.telemetry_client import TelemetryClient
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.external.logger import logger

TELEMETRY_API_KEY = os.environ.get(
    "CODECARBON_TELEMETRY_API_KEY",
    "cpt_sDiIpdwl5BRUM2T6vIJrt2JjL-pB3b46v8cvpLwuroU",
)
TELEMETRY_API_URL = os.environ.get(
    "CODECARBON_TELEMETRY_API_URL", "https://api.codecarbon.io"
)
TELEMETRY_EXPERIMENT_ID = None

_TIER1_SENT = False

def build_minimal_telemetry_dict(conf: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal telemetry payload dict from tracker configuration.

    Args:
        conf: Tracker configuration dictionary.

    Returns:
        Dictionary suitable for ``TelemetryCreate`` validation.
    """
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc),
        "telemetry_level": TelemetryLevel.minimal.value,
        "os": conf.get("os"),
        "country_iso_code": conf.get("country_iso_code"),
        "region": conf.get("region"),
        "cloud_provider": conf.get("provider"),
        "cloud_region": conf.get("region"),
        "longitude": conf.get("longitude"),
        "latitude": conf.get("latitude"),
        "cpu_count": conf.get("cpu_count"),
        "cpu_physical_count": conf.get("cpu_physical_count"),
        "cpu_model": conf.get("cpu_model"),
        "gpu_count": conf.get("gpu_count"),
        "gpu_model": conf.get("gpu_model"),
        "ram_total_size_gb": conf.get("ram_total_size"),
        "python_version": conf.get("python_version"),
        "codecarbon_version": conf.get("codecarbon_version"),
    }
    return {key: value for key, value in payload.items() if value is not None}


collect_tier1_payload = build_minimal_telemetry_dict


def send_tier1_telemetry(
    conf: dict[str, Any], endpoint_url: str | None = None
) -> bool:
    """Send minimal telemetry once per Python session.

    Args:
        conf: Tracker configuration dictionary.
        endpoint_url: Optional API base URL override.

    Returns:
        True if telemetry was sent successfully on this call, False if already
        sent in this session or if sending failed.
    """
    global _TIER1_SENT
    if _TIER1_SENT:
        return False
    try:
        payload = build_minimal_telemetry_dict(conf)
        client = TelemetryClient(
            endpoint_url=endpoint_url or TELEMETRY_API_URL,
            telemetry=payload,
        )
        if TELEMETRY_API_KEY:
            client.headers["x-api-token"] = TELEMETRY_API_KEY
        result = client.add_telemetry()
        if result is not None:
            _TIER1_SENT = True
            return True
        return False
    except Exception as error:
        logger.error(f"Telemetry Tier 1 failed (non-critical): {error}")
        return False
