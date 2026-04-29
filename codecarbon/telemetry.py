"""
Telemetry module for CodeCarbon.

This module handles two tiers of telemetry:
- Tier 1: Basic system information (always enabled) - python_version, os, cpu, gpu, ram, codecarbon_version, tracking_mode
- Tier 2: Detailed emissions data (opt-in) - requires CODECARBON_TELEMETRY_EXPERIMENT_ID environment variable
"""

import os
from typing import Any
import requests

from codecarbon.external.logger import logger

# Public telemetry API key - limited permissions for metrics only
TELEMETRY_API_KEY = os.environ.get(
    "CODECARBON_TELEMETRY_API_KEY",
    "cpt_sDiIpdwl5BRUM2T6vIJrt2JjL-pB3b46v8cvpLwuroU"
)
TELEMETRY_API_URL = "https://api.codecarbon.io"
TELEMETRY_EXPERIMENT_ID = None  # Set before enabling Tier 2 (see Task 4)

_TIER1_SENT = False  # module-level dedup: send once per Python session

_TIER1_FIELDS = [
    "python_version",
    "os",
    "cpu_count",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "ram_total_size",
    "codecarbon_version",
    "tracking_mode",
]


def collect_tier1_payload(conf: dict[str, Any]) -> dict[str, Any]:
    return {k: conf.get(k) for k in _TIER1_FIELDS}


def send_tier1_telemetry(conf: dict[str, Any]) -> bool:
    """Send Tier 1 telemetry metadata once per session.

    Posts environment metadata to the telemetry API endpoint. Uses module-level
    deduplication flag to ensure data is sent only once per Python session.
    Exceptions are caught and logged but not raised (silent fail).

    Args:
        conf: Configuration dict with environment metadata (keys: python_version,
              os, cpu_count, cpu_model, gpu_count, gpu_model, ram_total_size,
              codecarbon_version, tracking_mode)

    Returns:
        True if telemetry was sent successfully on this call, False if already
        sent in this session or if an error occurred.
    """
    global _TIER1_SENT
    if _TIER1_SENT:
        return False
    try:
        payload = collect_tier1_payload(conf)
        requests.post(
            f"{TELEMETRY_API_URL}/telemetry",
            json=payload,
            headers={"x-api-token": TELEMETRY_API_KEY},
            timeout=2,
        )
        _TIER1_SENT = True
        return True
    except Exception as e:
        logger.error(f"Telemetry Tier 1 failed (non-critical): {e}")
        return False
