"""
Telemetry configuration module.

Handles the 3-tier telemetry system:
- off: No telemetry
- internal: Private telemetry (helps CodeCarbon improve)  
- public: Public telemetry (shares emissions for leaderboard)

For Tier 1 (internal): POST to /telemetry endpoint.
For Tier 2 (public): POST /emissions uses a telemetry-only auth chain (env, JSON, preference,
``DEFAULT_PUBLIC_TELEMETRY_TOKEN``); hierarchical ``api_key`` is for dashboard/API logging only.

Telemetry base URL: env ``CODECARBON_TELEMETRY_API_ENDPOINT``, JSON ``telemetry_api_endpoint``,
then hierarchical ``api_endpoint`` (default ``https://api.codecarbon.io``).
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

TELEMETRY_API_ENDPOINT_ENV_VAR = "CODECARBON_TELEMETRY_API_ENDPOINT"
TELEMETRY_API_KEY_ENV_VAR = "CODECARBON_TELEMETRY_API_KEY"

# Default API base URL when hierarchical config has no api_endpoint (same default as EmissionsTracker)
DEFAULT_API_ENDPOINT = "https://api.codecarbon.io"

# Shared ingest token for public-tier POST /emissions when no user-specific telemetry token is set.
DEFAULT_PUBLIC_TELEMETRY_TOKEN: str = ""


class TelemetryTier(str, Enum):
    """Telemetry tiers."""

    OFF = "off"
    INTERNAL = "internal"
    PUBLIC = "public"


@dataclass
class TelemetryConfig:
    """Telemetry configuration.

    Attributes:
        project_token: Resolved value for telemetry ``x-api-token`` when set; independent of
            dashboard ``api_key`` / ``CODECARBON_API_KEY``.
    """

    tier: TelemetryTier
    project_token: Optional[str]
    api_endpoint: Optional[str]
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


def _hierarchical_config_dict() -> dict:
    """Load hierarchical CodeCarbon config (indirection for tests)."""
    from codecarbon.core.config import get_hierarchical_config

    return get_hierarchical_config()


def get_telemetry_auth_token() -> Optional[str]:
    """Resolve ``x-api-token`` for telemetry ``POST /telemetry`` (optional) and ``POST /emissions``.

    Order:
        1. Environment variable ``CODECARBON_TELEMETRY_API_KEY``
        2. ``telemetry_api_key`` or ``telemetry_project_token`` in ``[codecarbon]`` telemetry JSON
        3. ``project_token=`` line in telemetry preference file (legacy)
        4. :data:`DEFAULT_PUBLIC_TELEMETRY_TOKEN` when non-empty

    Hierarchical ``api_key`` / ``CODECARBON_API_KEY`` is not consulted (dashboard only).

    Returns:
        Token string or None if nothing is configured.
    """
    env_val = os.environ.get(TELEMETRY_API_KEY_ENV_VAR, "").strip()
    if env_val:
        return env_val

    try:
        from codecarbon.cli.cli_utils import load_telemetry_config_from_file

        json_config = load_telemetry_config_from_file()
        if json_config:
            for key in ("telemetry_api_key", "telemetry_project_token"):
                raw = json_config.get(key)
                if raw:
                    s = str(raw).strip()
                    if s:
                        return s
    except Exception:
        pass

    pref_file = get_telemetry_preference_file()
    if pref_file.exists():
        try:
            content = pref_file.read_text()
            lines = content.split("\n")
            for line in lines[2:]:
                if line.startswith("project_token="):
                    s = line.split("=", 1)[1].strip()
                    if s:
                        return s
        except Exception as e:
            logger.debug(f"Could not parse telemetry project token: {e}")

    if DEFAULT_PUBLIC_TELEMETRY_TOKEN.strip():
        return DEFAULT_PUBLIC_TELEMETRY_TOKEN.strip()

    return None


def get_public_telemetry_auth_token() -> Optional[str]:
    """Alias for :func:`get_telemetry_auth_token`."""
    return get_telemetry_auth_token()


def get_telemetry_project_token() -> Optional[str]:
    """Deprecated name; use :func:`get_telemetry_auth_token`."""
    return get_telemetry_auth_token()


def save_telemetry_project_token(token: str) -> None:
    """Save telemetry project token to JSON config file."""
    try:
        from codecarbon.cli.cli_utils import save_telemetry_config_to_file
        save_telemetry_config_to_file(project_token=token)
        logger.info("Saved telemetry project token to JSON config")
    except Exception as e:
        logger.warning(f"Failed to save to JSON config: {e}, using legacy format")
        # Fallback to legacy text format
        pref_file = get_telemetry_preference_file()
        existing_content = ""
        if pref_file.exists():
            existing_content = pref_file.read_text()
        
        lines = existing_content.split("\n")
        new_lines = []
        found_token = False
        for line in lines:
            if line.startswith("project_token="):
                new_lines.append(f"project_token={token}")
                found_token = True
            else:
                new_lines.append(line)
        
        if not found_token:
            new_lines.append(f"project_token={token}")
        
        pref_file.write_text("\n".join(new_lines))
        logger.info("Saved telemetry project token")


def get_telemetry_api_endpoint() -> Optional[str]:
    """Resolve telemetry HTTP base URL (no trailing slash in return value).

    Order:
        1. Environment variable ``CODECARBON_TELEMETRY_API_ENDPOINT``
        2. ``telemetry_api_endpoint`` in ``[codecarbon]`` telemetry JSON
        3. Hierarchical ``api_endpoint`` (same as tracker / dashboard default host)
    """
    env_val = os.environ.get(TELEMETRY_API_ENDPOINT_ENV_VAR, "").strip()
    if env_val:
        return env_val.rstrip("/")

    try:
        from codecarbon.cli.cli_utils import load_telemetry_config_from_file

        json_config = load_telemetry_config_from_file()
        raw = (json_config or {}).get("telemetry_api_endpoint")
        if raw:
            s = str(raw).strip().rstrip("/")
            if s:
                return s
    except Exception:
        pass

    try:
        conf = _hierarchical_config_dict()
        raw = conf.get("api_endpoint")
        if raw:
            s = str(raw).strip().rstrip("/")
            if s:
                return s
    except Exception:
        pass
    return None


def resolve_telemetry_base_url(api_endpoint: Optional[str]) -> str:
    """Return normalized base URL for telemetry HTTP requests (no trailing slash)."""
    base = (api_endpoint or DEFAULT_API_ENDPOINT).strip()
    return base.rstrip("/")


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
    # Get common config values
    project_token = get_telemetry_auth_token()
    api_endpoint = get_telemetry_api_endpoint()

    # Check environment variable first
    tier = detect_tier_from_env()
    if tier is not None:
        return TelemetryConfig(
            tier=tier,
            project_token=project_token,
            api_endpoint=api_endpoint,
            has_consent=True,
            first_run=False,
        )

    # Check saved preference
    saved = load_telemetry_preference()
    if saved is not None:
        tier, dont_ask = saved
        return TelemetryConfig(
            tier=tier,
            project_token=project_token,
            api_endpoint=api_endpoint,
            has_consent=True,
            first_run=False,
        )

    # First run - default to internal (telemetry enabled by default to help CodeCarbon improve)
    return TelemetryConfig(
        tier=TelemetryTier.INTERNAL,
        project_token=project_token,
        api_endpoint=api_endpoint,
        has_consent=True,
        first_run=True,
    )


def set_telemetry_tier(tier: TelemetryTier, dont_ask_again: bool = False) -> None:
    """Set the telemetry tier."""
    save_telemetry_preference(tier, dont_ask_again)
