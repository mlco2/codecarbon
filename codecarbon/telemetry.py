"""Product telemetry sent at tracker stop (Tier 1 private, Tier 2 public emissions)."""

import dataclasses
from typing import Any

from codecarbon.core.api_client import ApiClient
from codecarbon.core.telemetry_client import TelemetryClient
from codecarbon.core.telemetry_collect import build_tier1_payload
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import (
    get_telemetry_api_key,
    get_telemetry_api_url,
    get_telemetry_experiment_id,
    is_telemetry_level_explicit,
)
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

_TELEMETRY_CONFIGURE_WARNED = False

TELEMETRY_NOT_CONFIGURED_MESSAGE = (
    "CodeCarbon telemetry_level was not set explicitly; using default %r. "
    "Tier 1 private telemetry (per run at stop) will be sent. Set telemetry_level "
    "in .codecarbon.config, set CODECARBON_TELEMETRY_LEVEL, pass telemetry_level=... "
    "to EmissionsTracker / OfflineEmissionsTracker, or run "
    "codecarbon telemetry set <level>."
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


def _run_too_short_for_telemetry(emissions: EmissionsData) -> bool:
    return emissions.duration is not None and emissions.duration < 1


def send_tier1_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """Send Tier 1 telemetry: private hardware/usage/run summary via ``POST /telemetry``.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        external_conf: Merged config for telemetry API URL and key resolution.

    Returns:
        True if Tier 1 was accepted, False otherwise.
    """
    if _run_too_short_for_telemetry(emissions):
        logger.debug(
            "Tier 1 telemetry not sent because run duration is shorter than 1 second."
        )
        return False
    settings_conf = external_conf or {}
    try:
        payload = build_tier1_payload(tracker, emissions)
        client = TelemetryClient(
            endpoint_url=get_telemetry_api_url(settings_conf),
            telemetry=payload,
            api_key=get_telemetry_api_key(settings_conf),
        )
        return client.add_telemetry() is not None
    except Exception as error:
        logger.error(f"Tier 1 telemetry failed (non-critical): {error}")
        return False


def send_tier2_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """Send Tier 2 telemetry: run emissions to the shared experiment via ``ApiClient``.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        external_conf: Merged config for API URL, key, and experiment resolution.

    Returns:
        True if Tier 2 was posted successfully, False otherwise.
    """
    if _run_too_short_for_telemetry(emissions):
        logger.debug(
            "Tier 2 telemetry not sent because run duration is shorter than 1 second."
        )
        return False
    settings_conf = external_conf or {}
    conf = getattr(tracker, "_conf", {})
    try:
        api = ApiClient(
            endpoint_url=get_telemetry_api_url(settings_conf),
            experiment_id=get_telemetry_experiment_id(settings_conf),
            api_key=get_telemetry_api_key(settings_conf),
            conf=conf,
            create_run_automatically=True,
        )
        return bool(api.add_emission(dataclasses.asdict(emissions)))
    except Exception as error:
        logger.error(f"Tier 2 telemetry failed (non-critical): {error}")
        return False


def send_product_telemetry_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    level: TelemetryLevel,
    external_conf: dict[str, Any] | None = None,
) -> None:
    """Send product telemetry for the resolved tier at tracker ``stop()``.

    Tier 1 (``minimal``): private ``POST /telemetry`` only.
    Tier 2 (``extensive``): Tier 1 plus ``ApiClient`` run summary.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        level: Resolved ``TelemetryLevel``.
        external_conf: Merged config for API settings.
    """
    if level == TelemetryLevel.disabled:
        return
    settings = external_conf or {}
    if level in (TelemetryLevel.minimal, TelemetryLevel.extensive):
        send_tier1_at_stop(tracker, emissions, settings)
    if level == TelemetryLevel.extensive:
        send_tier2_at_stop(tracker, emissions, settings)
