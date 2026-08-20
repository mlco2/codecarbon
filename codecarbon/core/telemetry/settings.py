"""Resolve telemetry tier and API settings from config and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.external.logger import logger

DEFAULT_TELEMETRY_API_URL = "https://api.codecarbon.io"
DEFAULT_TELEMETRY_EXPERIMENT_ID = "d2d69403-1373-42b4-a2c1-09589aed4801"
DEFAULT_TELEMETRY_LEVEL = TelemetryLevel.minimal

TELEMETRY_LEVEL_CONFIG_KEY = "telemetry_level"

# (settings attribute, config keys, environment variable, default)
_CONNECTION_FIELDS = (
    (
        "api_url",
        ("telemetry_api_url", "api_endpoint"),
        "CODECARBON_TELEMETRY_API_URL",
        DEFAULT_TELEMETRY_API_URL,
    ),
    ("api_key", ("telemetry_api_key",), "CODECARBON_TELEMETRY_API_KEY", None),
    (
        "experiment_id",
        ("telemetry_experiment_id",),
        "CODECARBON_TELEMETRY_EXPERIMENT_ID",
        DEFAULT_TELEMETRY_EXPERIMENT_ID,
    ),
)


def parse_telemetry_level(raw: str | TelemetryLevel) -> TelemetryLevel:
    """Parse a telemetry tier name or enum member."""
    if isinstance(raw, TelemetryLevel):
        return raw
    try:
        return TelemetryLevel(str(raw).lower())
    except ValueError as error:
        raise ValueError(
            f"Invalid telemetry_level {raw!r}. Choose: disabled, minimal, or extensive."
        ) from error


@dataclass(frozen=True)
class TelemetrySettings:
    """Resolved telemetry tier and API connection settings."""

    level: TelemetryLevel
    is_explicit: bool
    api_url: str
    api_key: str | None
    experiment_id: str

    @classmethod
    def resolve(
        cls,
        *,
        external_conf: dict[str, Any] | None = None,
        override: str | TelemetryLevel | None = None,
    ) -> TelemetrySettings:
        """Resolve tier (override > config/env > default minimal) and API settings."""
        conf = external_conf or {}
        raw = (
            override
            if override is not None
            else conf.get(TELEMETRY_LEVEL_CONFIG_KEY) or None
        )
        level = DEFAULT_TELEMETRY_LEVEL
        if raw is not None:
            try:
                level = parse_telemetry_level(raw)
            except ValueError:
                logger.error(
                    "Invalid telemetry_level provided; falling back to %r",
                    DEFAULT_TELEMETRY_LEVEL.value,
                )
        connection = {
            name: next(
                (conf[key] for key in keys if conf.get(key)),
                os.environ.get(env) or default,
            )
            for name, keys, env, default in _CONNECTION_FIELDS
        }
        connection["api_url"] = connection["api_url"].rstrip("/")
        return cls(level=level, is_explicit=raw is not None, **connection)
