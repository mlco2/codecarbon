"""
Telemetry configuration module.

Handles the 3-tier telemetry system:
- off: No telemetry
- internal: Private telemetry (helps CodeCarbon improve)  
- public: Public telemetry (shares emissions for leaderboard)
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import appdirs

from codecarbon.external.logger import logger

# Environment variable name for telemetry setting
TELEMETRY_ENV_VAR = "CODECARBON_TELEMETRY"

# Environment variable for OTEL endpoint
OTEL_ENDPOINT_ENV_VAR = "CODECARBON_OTEL_ENDPOINT"

# Default OTEL endpoint (can be configured by CodeCarbon team)
DEFAULT_OTEL_ENDPOINT = "https://otlp.example.com/v1/traces"


class TelemetryTier(str, Enum):
    """Telemetry tiers."""

    OFF = "off"
    INTERNAL = "internal"
    PUBLIC = "public"


@dataclass
class TelemetryConfig:
    """Telemetry configuration."""

    tier: TelemetryTier
    otel_endpoint: Optional[str]
    has_consent: bool
    first_run: bool

    @property
    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self.tier != TelemetryTier.OFF

    @property
    def is_public(self) -> bool:
        """Check if public telemetry (emissions shared)."""
        return self.tier == TelemetryTier.PUBLIC

    @property
    def is_internal(self) -> bool:
        """Check if internal telemetry (private)."""
        return self.tier == TelemetryTier.INTERNAL


def get_user_config_dir() -> Path:
    """Get the user config directory."""
    return Path(appdirs.user_config_dir("codecarbon", "CodeCarbon"))


def get_telemetry_preference_file() -> Path:
    """Get the file path for storing telemetry preference."""
    return get_user_config_dir() / "telemetry_preference.txt"


def save_telemetry_preference(tier: TelemetryTier, dont_ask_again: bool = False) -> None:
    """Save user's telemetry preference."""
    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    pref_file = get_telemetry_preference_file()
    content = f"{tier.value}\n"
    if dont_ask_again:
        content += "dont_ask_again\n"
    pref_file.write_text(content)
    logger.info(f"Saved telemetry preference: {tier.value}")


def load_telemetry_preference() -> Optional[tuple[TelemetryTier, bool]]:
    """Load user's saved telemetry preference.
    
    Returns:
        Tuple of (tier, dont_ask_again) or None if not set.
    """
    pref_file = get_telemetry_preference_file()
    if not pref_file.exists():
        return None

    try:
        content = pref_file.read_text().strip()
        lines = content.split("\n")
        tier = TelemetryTier(lines[0])
        dont_ask_again = len(lines) > 1 and "dont_ask_again" in lines[1]
        return (tier, dont_ask_again)
    except (ValueError, IndexError) as e:
        logger.debug(f"Could not parse telemetry preference: {e}")
        return None


def detect_tier_from_env() -> Optional[TelemetryTier]:
    """Detect telemetry tier from environment variable."""
    env_value = os.environ.get(TELEMETRY_ENV_VAR, "").lower().strip()
    if not env_value:
        return None

    try:
        return TelemetryTier(env_value)
    except ValueError:
        logger.warning(
            f"Invalid CODECARBON_TELEMETRY value: {env_value}. "
            f"Valid values: {', '.join(t.value for t in TelemetryTier)}"
        )
        return None


def get_otel_endpoint() -> Optional[str]:
    """Get OTEL endpoint from environment or return None for default."""
    return os.environ.get(OTEL_ENDPOINT_ENV_VAR)


def get_telemetry_config(force_first_run: bool = False) -> TelemetryConfig:
    """
    Get the telemetry configuration.

    Priority order:
    1. Environment variable (CODECARBON_TELEMETRY)
    2. Saved user preference
    3. Default to internal (first run) - telemetry enabled by default

    Args:
        force_first_run: Force treating this as first run (for testing)

    Returns:
        TelemetryConfig object
    """
    # Check environment variable first
    tier = detect_tier_from_env()
    if tier is not None:
        return TelemetryConfig(
            tier=tier,
            otel_endpoint=get_otel_endpoint(),
            has_consent=True,
            first_run=False,
        )

    # Check saved preference
    saved = load_telemetry_preference()
    if saved is not None:
        tier, dont_ask = saved
        return TelemetryConfig(
            tier=tier,
            otel_endpoint=get_otel_endpoint(),
            has_consent=True,
            first_run=False,
        )

    # First run - default to internal (telemetry enabled by default to help CodeCarbon improve)
    return TelemetryConfig(
        tier=TelemetryTier.INTERNAL,
        otel_endpoint=get_otel_endpoint(),
        has_consent=True,
        first_run=True,
    )


def set_telemetry_tier(tier: TelemetryTier, dont_ask_again: bool = False) -> None:
    """Set the telemetry tier."""
    save_telemetry_preference(tier, dont_ask_again)
