"""Resolve telemetry tier and API URL from config and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.external.logger import logger

DEFAULT_TELEMETRY_API_URL = "https://api.codecarbon.io"
DEFAULT_TELEMETRY_LEVEL = TelemetryLevel.minimal

TELEMETRY_LEVEL_CONFIG_KEY = "telemetry_level"

API_URL_CONFIG_KEYS = ("telemetry_api_url", "api_endpoint")
API_URL_ENV_VAR = "CODECARBON_TELEMETRY_API_URL"


def parse_telemetry_level(raw: str | TelemetryLevel) -> TelemetryLevel:
    """Parse a telemetry tier name or enum member."""
    if isinstance(raw, TelemetryLevel):
        return raw
    try:
        return TelemetryLevel(str(raw).lower())
    except ValueError as error:
        raise ValueError(
            f"Invalid telemetry_level {raw!r}. Choose: disabled or minimal."
        ) from error


@dataclass(frozen=True)
class TelemetrySettings:
    """Resolved telemetry tier and API URL."""

    level: TelemetryLevel
    is_explicit: bool
    api_url: str

    @classmethod
    def resolve(
        cls,
        *,
        external_conf: dict[str, Any] | None = None,
        override: str | TelemetryLevel | None = None,
    ) -> TelemetrySettings:
        """Resolve tier (override > config/env > default minimal) and API URL."""
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
        api_url = next(
            (conf[key] for key in API_URL_CONFIG_KEYS if conf.get(key)),
            os.environ.get(API_URL_ENV_VAR) or DEFAULT_TELEMETRY_API_URL,
        )
        return cls(
            level=level, is_explicit=raw is not None, api_url=api_url.rstrip("/")
        )
