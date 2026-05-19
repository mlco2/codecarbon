"""Resolve telemetry tier and API settings from config and environment."""

import os
from typing import Any

from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.external.logger import logger

DEFAULT_TELEMETRY_API_URL = "https://api.codecarbon.io"
DEFAULT_TELEMETRY_API_KEY = "cpt_JZhj-vJdEVG28qErZL5mh1ftiqbnDIBYjWSxwvX3rfI"
DEFAULT_TELEMETRY_EXPERIMENT_ID = "aa69b440-014a-4562-ac06-ba7eecb023f9"
DEFAULT_TELEMETRY_LEVEL = TelemetryLevel.minimal

TELEMETRY_LEVEL_CONFIG_KEY = "telemetry_level"


def parse_telemetry_level(raw: str | TelemetryLevel) -> TelemetryLevel:
    """Parse a telemetry tier from a string or enum value.

    Args:
        raw: Tier name or ``TelemetryLevel`` member.

    Returns:
        Parsed ``TelemetryLevel``.

    Raises:
        ValueError: If ``raw`` is not a valid tier name.
    """
    if isinstance(raw, TelemetryLevel):
        return raw
    try:
        return TelemetryLevel(str(raw).lower())
    except ValueError as error:
        raise ValueError(
            f"Invalid telemetry_level {raw!r}. Choose: disabled, minimal, or extensive."
        ) from error


def is_telemetry_level_explicit(
    config_file_conf: dict[str, Any],
    *,
    override: str | TelemetryLevel | None = None,
    external_conf: dict[str, Any] | None = None,
) -> bool:
    """Return whether the user explicitly chose a telemetry tier.

    Explicit sources: tracker ``telemetry_level`` argument, config file
    ``telemetry_level``, or environment ``CODECARBON_TELEMETRY_LEVEL``.

    Args:
        config_file_conf: Settings from ``get_config_file_settings()`` (no env overlay).
        override: Value passed to ``EmissionsTracker(telemetry_level=...)``.
        external_conf: Merged config from file and environment.

    Returns:
        True if any explicit source is set.
    """
    if override is not None:
        return True
    if config_file_conf.get(TELEMETRY_LEVEL_CONFIG_KEY) is not None:
        return True
    if external_conf is None:
        return False
    return external_conf.get(TELEMETRY_LEVEL_CONFIG_KEY) is not None


def resolve_telemetry_level(
    config_file_conf: dict[str, Any] | None = None,
    *,
    override: str | TelemetryLevel | None = None,
    external_conf: dict[str, Any] | None = None,
) -> TelemetryLevel:
    """Resolve the active telemetry tier.

    Precedence:

        1. ``override`` — ``EmissionsTracker(telemetry_level=...)`` or CLI
        2. ``external_conf`` — merged ``.codecarbon.config`` and ``CODECARBON_*`` env
        3. ``config_file_conf`` — file-only settings when ``external_conf`` is omitted
        4. Default: ``minimal`` (Tier 1)

    Args:
        config_file_conf: Settings from ``get_config_file_settings()`` (optional).
        override: Optional tier from tracker or CLI.
        external_conf: Merged settings from ``get_hierarchical_config()`` (optional).

    Returns:
        Resolved ``TelemetryLevel``.
    """
    if override is not None:
        raw = override
    elif external_conf is not None and external_conf.get(TELEMETRY_LEVEL_CONFIG_KEY) is not None:
        raw = external_conf[TELEMETRY_LEVEL_CONFIG_KEY]
    elif config_file_conf is not None and config_file_conf.get(
        TELEMETRY_LEVEL_CONFIG_KEY
    ) is not None:
        raw = config_file_conf[TELEMETRY_LEVEL_CONFIG_KEY]
    else:
        return DEFAULT_TELEMETRY_LEVEL
    try:
        return parse_telemetry_level(raw)
    except ValueError:
        logger.error(
            "Invalid telemetry_level %r; falling back to %r",
            raw,
            DEFAULT_TELEMETRY_LEVEL.value,
        )
        return DEFAULT_TELEMETRY_LEVEL


def get_telemetry_api_url(
    external_conf: dict[str, Any],
    default: str = DEFAULT_TELEMETRY_API_URL,
) -> str:
    """Return telemetry API base URL from config or environment.

    Args:
        external_conf: Merged config from file and environment.
        default: URL used when unset.

    Returns:
        API base URL without trailing slash.
    """
    url = (
        external_conf.get("telemetry_api_url")
        or external_conf.get("api_endpoint")
        or os.environ.get("CODECARBON_TELEMETRY_API_URL")
    )
    return (url or default).rstrip("/")


def get_telemetry_api_key(external_conf: dict[str, Any]) -> str:
    """Return telemetry API token from config, environment, or public default.

    Args:
        external_conf: Merged config from file and environment.

    Returns:
        API token string.
    """
    key = (
        external_conf.get("telemetry_api_key")
        or external_conf.get("api_key")
        or os.environ.get("CODECARBON_TELEMETRY_API_KEY")
    )
    return key or DEFAULT_TELEMETRY_API_KEY


def get_telemetry_experiment_id(external_conf: dict[str, Any]) -> str:
    """Return telemetry experiment id from config, environment, or public default.

    Args:
        external_conf: Merged config from file and environment.

    Returns:
        Experiment UUID string (legacy leaderboard / API helpers).
    """
    experiment_id = external_conf.get("telemetry_experiment_id") or os.environ.get(
        "CODECARBON_TELEMETRY_EXPERIMENT_ID"
    )
    return experiment_id or DEFAULT_TELEMETRY_EXPERIMENT_ID
