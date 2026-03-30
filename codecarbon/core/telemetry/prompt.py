"""
First-run prompt for telemetry consent.

Shows an interactive prompt to let users choose their telemetry level.
"""

from typing import Optional

from codecarbon.core.telemetry.config import (
    TelemetryTier,
    get_telemetry_config,
    save_telemetry_preference,
)
from codecarbon.external.logger import logger

# Try to import rich/questionary for interactive prompts
# Falls back to simple input if not available
try:
    from rich.console import Console
    from rich.prompt import Prompt

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import questionary

    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


console = Console() if RICH_AVAILABLE else None


def prompt_for_telemetry_consent() -> Optional[TelemetryTier]:
    """
    Prompt user for telemetry consent on first run.
    
    Returns:
        The chosen TelemetryTier, or None if prompt should not be shown.
    """
    config = get_telemetry_config()

    # Don't prompt if consent already given via env var or saved preference
    if config.has_consent:
        return config.tier

    # Check if we should prompt (first run without saved preference)
    if not config.first_run:
        return config.tier

    # Try interactive prompt, but don't fail if not available
    if QUESTIONARY_AVAILABLE:
        return _prompt_interactive_questionary()
    elif RICH_AVAILABLE:
        return _prompt_interactive_rich()
    else:
        return _prompt_simple()


def _prompt_interactive_questionary() -> Optional[TelemetryTier]:
    """Prompt using questionary library."""
    try:
        answer = questionary.select(
            "📊 CodeCarbon Telemetry\n\n"
            "Help improve CodeCarbon by sharing anonymous usage data?\n",
            choices=[
                "Internal - Basic environment info (PRIVATE)",
                "Public - Full telemetry (SHARED PUBLICLY on leaderboard)",
                "Off - No telemetry",
            ],
            default="Internal - Basic environment info (PRIVATE)",
        ).ask()

        if answer is None:
            return TelemetryTier.OFF

        if "Internal" in answer:
            return TelemetryTier.INTERNAL
        elif "Public" in answer:
            return TelemetryTier.PUBLIC
        else:
            return TelemetryTier.OFF
    except Exception as e:
        logger.debug(f"Questionary prompt failed: {e}")
        return TelemetryTier.OFF


def _prompt_interactive_rich() -> Optional[TelemetryTier]:
    """Prompt using rich library."""
    if console is None:
        return TelemetryTier.OFF

    try:
        console.print("\n📊 [bold]CodeCarbon Telemetry[/bold]\n")
        console.print(
            "Help improve CodeCarbon by sharing anonymous usage data?\n"
        )
        console.print("  [1] Internal - Basic environment info (PRIVATE)")
        console.print("      • Python version, OS, CPU/GPU hardware")
        console.print("      • Usage patterns, ML frameworks")
        console.print("      • Helps us improve the library")
        console.print()
        console.print("  [2] Public - Full telemetry (SHARED PUBLICLY)")
        console.print("      • All of internal + emissions data")
        console.print("      • Shown on public leaderboard")
        console.print()
        console.print("  [3] Off - No telemetry")
        console.print()

        answer = Prompt.ask(
            "Select option",
            choices=["1", "2", "3"],
            default="1",
        )

        if answer == "1":
            return TelemetryTier.INTERNAL
        elif answer == "2":
            return TelemetryTier.PUBLIC
        else:
            return TelemetryTier.OFF
    except Exception as e:
        logger.debug(f"Rich prompt failed: {e}")
        return TelemetryTier.OFF


def _prompt_simple() -> Optional[TelemetryTier]:
    """Simple input-based prompt."""
    try:
        print("\n📊 CodeCarbon Telemetry")
        print("=" * 40)
        print("Help improve CodeCarbon by sharing anonymous usage data?")
        print()
        print("  1) Internal - Basic environment info (PRIVATE)")
        print("  2) Public - Full telemetry (SHARED PUBLICLY)")
        print("  3) Off - No telemetry")
        print()
        answer = input("Select option [1]: ").strip() or "1"

        if answer == "1":
            return TelemetryTier.INTERNAL
        elif answer == "2":
            return TelemetryTier.PUBLIC
        else:
            return TelemetryTier.OFF
    except Exception as e:
        logger.debug(f"Simple prompt failed: {e}")
        return TelemetryTier.OFF


def prompt_and_save() -> TelemetryTier:
    """
    Prompt user and save their choice.
    
    Returns:
        The chosen TelemetryTier.
    """
    tier = prompt_for_telemetry_consent()
    
    if tier is None:
        tier = TelemetryTier.OFF
    
    # Save the preference (don't ask again)
    save_telemetry_preference(tier, dont_ask_again=True)
    
    return tier
