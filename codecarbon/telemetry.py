"""Tracker-facing telemetry helpers (Tier 1 HTTP, Tier 2 public emissions)."""

import dataclasses
from datetime import datetime, timezone
from typing import Any

from codecarbon.core.api_client import ApiClient
from codecarbon.core.telemetry_client import TelemetryClient
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import (
    get_telemetry_api_key,
    get_telemetry_api_url,
    get_telemetry_experiment_id,
    is_telemetry_level_explicit,
)
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

_TIER1_SENT = False
_TIER2_SENT = False
_TELEMETRY_CONFIGURE_WARNED = False

TELEMETRY_NOT_CONFIGURED_MESSAGE = (
    "CodeCarbon telemetry_level was not set explicitly; using default %r. "
    "Tier 1 minimal telemetry (hardware and environment metadata) will be "
    "sent once per Python session. Set telemetry_level in .codecarbon.config "
    "(disabled, minimal, or extensive), pass telemetry_level=... to "
    "EmissionsTracker / OfflineEmissionsTracker, or set CODECARBON_TELEMETRY_LEVEL "
    "to opt out (disabled), keep minimal telemetry, or enable extensive (public "
    "emissions on stop)."
)


def warn_if_telemetry_not_configured(
    config_file_conf: dict[str, Any],
    active_level: TelemetryLevel,
    *,
    override: str | TelemetryLevel | None = None,
    external_conf: dict[str, Any] | None = None,
) -> None:
    """Log a one-time warning when telemetry tier was not set explicitly.

    Args:
        config_file_conf: File-only settings from ``get_config_file_settings()``.
        active_level: Resolved tier in use for this tracker.
        override: Optional ``telemetry_level`` tracker argument.
        external_conf: Merged file/env settings for explicit-env detection.
    """
    global _TELEMETRY_CONFIGURE_WARNED
    if _TELEMETRY_CONFIGURE_WARNED:
        return
    if is_telemetry_level_explicit(
        config_file_conf, override=override, external_conf=external_conf
    ):
        return
    logger.warning(
        TELEMETRY_NOT_CONFIGURED_MESSAGE,
        active_level.value,
    )
    _TELEMETRY_CONFIGURE_WARNED = True


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


def send_tier1_telemetry(
    conf: dict[str, Any],
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """POST minimal telemetry once per Python session via ``TelemetryClient``.

    Sends ``POST {telemetry_api_url}/telemetry`` with a ``TelemetryCreate`` payload
    built from tracker configuration. Best-effort: failures are logged and not raised.

    Args:
        conf: Tracker configuration dictionary.
        external_conf: Merged file/env config for telemetry API URL and key resolution.

    Returns:
        True if telemetry was posted successfully on this call, False if already sent
        in this session or if the request failed.
    """
    global _TIER1_SENT
    if _TIER1_SENT:
        return False
    settings_conf = external_conf or {}
    try:
        payload = build_minimal_telemetry_dict(conf)
        endpoint_url = get_telemetry_api_url(settings_conf)
        client = TelemetryClient(
            endpoint_url=endpoint_url,
            telemetry=payload,
            api_key=get_telemetry_api_key(settings_conf),
        )
        response = client.add_telemetry()
        if response is not None:
            _TIER1_SENT = True
            return True
        return False
    except Exception as error:
        logger.error(f"Telemetry Tier 1 failed (non-critical): {error}")
        return False


def send_tier2_public_emission(
    conf: dict[str, Any],
    emissions_data: EmissionsData,
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """Send run emissions to the public telemetry experiment via ApiClient.

    Mirrors ``CodeCarbonAPIOutput`` / ``add_emission`` for the shared leaderboard
    project. Best-effort: errors are logged and not raised.

    Args:
        conf: Tracker configuration dictionary.
        emissions_data: Delta or total emissions row for the run.
        external_conf: Merged file/env config for API URL, key, and experiment id.

    Returns:
        True if emission was posted successfully on this call, False otherwise.
    """
    global _TIER2_SENT
    if _TIER2_SENT:
        return False
    settings_conf = external_conf or {}
    try:
        api = ApiClient(
            endpoint_url=get_telemetry_api_url(settings_conf),
            experiment_id=get_telemetry_experiment_id(settings_conf),
            api_key=get_telemetry_api_key(settings_conf),
            conf=conf,
            create_run_automatically=True,
        )
        posted = api.add_emission(dataclasses.asdict(emissions_data))
        if posted:
            _TIER2_SENT = True
            return True
        return False
    except Exception as error:
        logger.error(f"Telemetry Tier 2 failed (non-critical): {error}")
        return False
