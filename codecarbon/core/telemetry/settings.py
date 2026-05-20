"""Resolve telemetry tier and API settings from config and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.external.logger import logger

DEFAULT_TELEMETRY_API_URL = "https://api.codecarbon.io"
DEFAULT_TELEMETRY_API_KEY = "cpt_sDiIpdwl5BRUM2T6vIJrt2JjL-pB3b46v8cvpLwuroU"
DEFAULT_TELEMETRY_EXPERIMENT_ID = "d2d69403-1373-42b4-a2c1-09589aed4801"
DEFAULT_TELEMETRY_LEVEL = TelemetryLevel.minimal

TELEMETRY_LEVEL_CONFIG_KEY = "telemetry_level"

TelemetryLevelSource = Literal["override", "external", "file", "default"]


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


@dataclass(frozen=True)
class TelemetrySettings:
    """Resolved telemetry tier and API connection settings."""

    level: TelemetryLevel
    source: TelemetryLevelSource
    api_url: str
    api_key: str
    experiment_id: str

    @property
    def is_explicit(self) -> bool:
        """Return whether the user explicitly chose a telemetry tier."""
        return self.source != "default"

    @classmethod
    def resolve(
        cls,
        *,
        config_file_conf: dict[str, Any] | None = None,
        external_conf: dict[str, Any] | None = None,
        override: str | TelemetryLevel | None = None,
    ) -> TelemetrySettings:
        """Resolve telemetry tier and API settings.

        Precedence for tier:

            1. ``override`` — ``EmissionsTracker(telemetry_level=...)`` or CLI
            2. ``external_conf`` — merged ``.codecarbon.config`` and env
            3. ``config_file_conf`` — file-only settings
            4. Default: ``minimal``

        Args:
            config_file_conf: Settings from ``get_config_file_settings()``.
            external_conf: Merged settings from ``get_hierarchical_config()``.
            override: Optional tier from tracker or CLI.

        Returns:
            Resolved settings bundle.
        """
        merged = external_conf or {}
        if override is not None:
            raw = override
            source: TelemetryLevelSource = "override"
        elif merged.get(TELEMETRY_LEVEL_CONFIG_KEY) is not None:
            raw = merged[TELEMETRY_LEVEL_CONFIG_KEY]
            source = "external"
        elif (
            config_file_conf is not None
            and config_file_conf.get(TELEMETRY_LEVEL_CONFIG_KEY) is not None
        ):
            raw = config_file_conf[TELEMETRY_LEVEL_CONFIG_KEY]
            source = "file"
        else:
            return cls(
                level=DEFAULT_TELEMETRY_LEVEL,
                source="default",
                api_url=cls._resolve_api_url(merged),
                api_key=cls._resolve_api_key(merged),
                experiment_id=cls._resolve_experiment_id(merged),
            )
        try:
            level = parse_telemetry_level(raw)
        except ValueError:
            logger.error(
                "Invalid telemetry_level %r; falling back to %r",
                raw,
                DEFAULT_TELEMETRY_LEVEL.value,
            )
            level = DEFAULT_TELEMETRY_LEVEL
        return cls(
            level=level,
            source=source,
            api_url=cls._resolve_api_url(merged),
            api_key=cls._resolve_api_key(merged),
            experiment_id=cls._resolve_experiment_id(merged),
        )

    @staticmethod
    def _resolve_api_url(external_conf: dict[str, Any]) -> str:
        url = (
            external_conf.get("telemetry_api_url")
            or external_conf.get("api_endpoint")
            or os.environ.get("CODECARBON_TELEMETRY_API_URL")
        )
        return (url or DEFAULT_TELEMETRY_API_URL).rstrip("/")

    @staticmethod
    def _resolve_api_key(external_conf: dict[str, Any]) -> str:
        key = (
            external_conf.get("telemetry_api_key")
            or external_conf.get("api_key")
            or os.environ.get("CODECARBON_TELEMETRY_API_KEY")
        )
        return key or DEFAULT_TELEMETRY_API_KEY

    @staticmethod
    def _resolve_experiment_id(external_conf: dict[str, Any]) -> str:
        experiment_id = external_conf.get("telemetry_experiment_id") or os.environ.get(
            "CODECARBON_TELEMETRY_EXPERIMENT_ID"
        )
        return experiment_id or DEFAULT_TELEMETRY_EXPERIMENT_ID
