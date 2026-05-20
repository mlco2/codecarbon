"""Product telemetry sent at tracker stop (Tier 1 / Tier 2)."""

import dataclasses
from typing import Any

from codecarbon.core.api_client import ApiClient
from codecarbon.core.telemetry_client import post_private_telemetry
from codecarbon.core.telemetry_collect import build_telemetry_payload
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import (
    get_telemetry_api_key,
    get_telemetry_api_url,
    get_telemetry_experiment_id,
    is_telemetry_level_explicit,
)
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData

TELEMETRY_NOT_CONFIGURED_MESSAGE = (
    "CodeCarbon telemetry_level was not set explicitly; using default %r. "
    "Tier 1 private telemetry (per run at stop) will be sent. Set telemetry_level "
    "in .codecarbon.config, set CODECARBON_TELEMETRY_LEVEL, pass telemetry_level=... "
    "to EmissionsTracker / OfflineEmissionsTracker, or run "
    "codecarbon telemetry set <level>."
)

_telemetry_default_warning_shown = False


def reset_telemetry_warning() -> None:
    """Clear the one-shot default-tier warning (for tests)."""
    global _telemetry_default_warning_shown
    _telemetry_default_warning_shown = False


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
    global _telemetry_default_warning_shown
    if is_telemetry_level_explicit(
        config_file_conf, override=override, external_conf=external_conf
    ):
        return
    if _telemetry_default_warning_shown:
        return
    logger.warning(TELEMETRY_NOT_CONFIGURED_MESSAGE, active_level.value)
    _telemetry_default_warning_shown = True


def send_private_telemetry_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    external_conf: dict[str, Any] | None = None,
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> bool:
    """Send Tier 1 private telemetry via ``POST /telemetry``.

    Runs shorter than one second are skipped by ``send_product_telemetry_at_stop``,
    not here; direct callers may still post for sub-second runs.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        external_conf: Merged config for telemetry API URL and key resolution.
        level: Resolved ``TelemetryLevel`` for the ``telemetry_level`` field.

    Returns:
        True if the private telemetry POST was accepted, False otherwise.
    """
    settings_conf = external_conf or {}
    try:
        payload = build_telemetry_payload(tracker, emissions, level=level)
        return post_private_telemetry(
            get_telemetry_api_url(settings_conf),
            payload,
            get_telemetry_api_key(settings_conf),
        )
    except Exception as error:
        logger.error(f"Private telemetry failed (non-critical): {error}")
        return False


def send_public_run_summary_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """Send Tier 2 public run summary to the shared telemetry experiment via ``ApiClient``.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        external_conf: Merged config for API URL, key, and experiment resolution.

    Returns:
        True if the run summary was posted successfully, False otherwise.
    """
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
        logger.error(f"Public run summary failed (non-critical): {error}")
        return False


def send_product_telemetry_at_stop(
    tracker: Any,
    emissions: EmissionsData,
    level: TelemetryLevel,
    external_conf: dict[str, Any] | None = None,
) -> None:
    """Send product telemetry for the resolved tier at tracker ``stop()``.

    Tier 1 (``minimal``): private ``POST /telemetry`` only.
    Tier 2 (``extensive``): same private ``POST /telemetry`` plus public run summary.

    Args:
        tracker: Active emissions tracker instance.
        emissions: Total emissions from ``_prepare_emissions_data()``.
        level: Resolved ``TelemetryLevel``.
        external_conf: Merged config for API settings.
    """
    if level == TelemetryLevel.disabled:
        return
    if emissions.duration is not None and emissions.duration < 1:
        logger.debug("Telemetry not sent: run shorter than 1 second.")
        return
    settings = external_conf or {}
    if level in (TelemetryLevel.minimal, TelemetryLevel.extensive):
        send_private_telemetry_at_stop(tracker, emissions, settings, level=level)
    if level == TelemetryLevel.extensive:
        send_public_run_summary_at_stop(tracker, emissions, settings)
