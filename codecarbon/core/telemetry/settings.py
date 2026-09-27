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

API_URL_CONFIG_KEYS = ("telemetry_api_url",)
API_URL_ENV_VAR = "CODECARBON_TELEMETRY_API_URL"


#: Older releases used a wider ``extensive`` tier; map it onto the tier that
#: replaced it rather than treating it as unparseable.
LEGACY_LEVEL_ALIASES = {"extensive": TelemetryLevel.minimal}


def parse_telemetry_level(raw: str | TelemetryLevel) -> TelemetryLevel:
    """Parse a telemetry tier name or enum member."""
    if isinstance(raw, TelemetryLevel):
        return raw
    normalized = str(raw).lower()
    if normalized in LEGACY_LEVEL_ALIASES:
        return LEGACY_LEVEL_ALIASES[normalized]
    try:
        return TelemetryLevel(normalized)
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
        raw = override if override is not None else conf.get(TELEMETRY_LEVEL_CONFIG_KEY)
        level = DEFAULT_TELEMETRY_LEVEL
        if raw is not None:
            try:
                level = parse_telemetry_level(raw)
            except ValueError:
                # An unrecognized value (typo, or a privacy-intent string like
                # "off"/"false"/"none"/"0") must never be treated as consent
                # to send telemetry: fail closed to disabled, not minimal.
                level = TelemetryLevel.disabled
                logger.error(
                    "Invalid telemetry_level %r; falling back to %r",
                    raw,
                    TelemetryLevel.disabled.value,
                )
        api_url = next(
            (conf[key] for key in API_URL_CONFIG_KEYS if conf.get(key)),
            os.environ.get(API_URL_ENV_VAR) or DEFAULT_TELEMETRY_API_URL,
        )
        return cls(
            level=level, is_explicit=raw is not None, api_url=api_url.rstrip("/")
        )
