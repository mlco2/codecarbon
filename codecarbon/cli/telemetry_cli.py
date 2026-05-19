"""CLI commands to configure CodeCarbon product telemetry tiers."""

from pathlib import Path
from typing import Optional

import questionary
import typer
from rich import print
from typing_extensions import Annotated

from codecarbon.cli.cli_utils import (
    create_new_config_file,
    get_config,
    overwrite_local_config,
)
from codecarbon.core.config import get_config_file_settings, get_hierarchical_config
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import (
    DEFAULT_TELEMETRY_LEVEL,
    is_telemetry_level_explicit,
    parse_telemetry_level,
    resolve_telemetry_level,
)

telemetry_app = typer.Typer(
    help="Configure product telemetry (disabled, minimal, or extensive).",
    no_args_is_help=False,
)

TIER_DESCRIPTIONS = {
    "disabled": "No telemetry.",
    "minimal": "Send hardware/environment metadata once per session (Tier 1).",
    "extensive": "Tier 1 plus public emissions on stop (Tier 2 leaderboard).",
}


def normalize_telemetry_level(level: str) -> str:
    """Validate and normalize a telemetry tier string for CLI use.

    Args:
        level: User-provided tier name.

    Returns:
        Canonical tier value.

    Raises:
        typer.BadParameter: If the level is not a valid ``TelemetryLevel``.
    """
    try:
        return parse_telemetry_level(level).value
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


def resolve_config_path(config: Optional[Path], *, create: bool = False) -> Path:
    """Resolve which config file to read or write.

    Args:
        config: Explicit path from ``--config``, if any.
        create: When True and no file exists, create ``./.codecarbon.config``.

    Returns:
        Resolved config file path.
    """
    if config is not None:
        path = config.expanduser().resolve()
        if create and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[codecarbon]\n", encoding="utf-8")
        return path
    local_path = Path.cwd().resolve() / ".codecarbon.config"
    if local_path.exists():
        return local_path
    global_path = (Path.home() / ".codecarbon.config").expanduser().resolve()
    if global_path.exists():
        return global_path
    if create:
        local_path.write_text("[codecarbon]\n", encoding="utf-8")
        return local_path
    return local_path


def pick_config_path_interactive() -> Path:
    """Prompt for which config file to update.

    Returns:
        Path chosen by the user.
    """
    home = Path.home()
    global_path = (home / ".codecarbon.config").expanduser().resolve()
    local_path = Path.cwd().resolve() / ".codecarbon.config"
    options = []
    if global_path.exists():
        options.append(str(global_path))
    if local_path.exists() and local_path not in options:
        options.append(str(local_path))
    options.append("Create new config file")
    if not options:
        options = ["Create new config file"]
    choice = questionary.select(
        "Which configuration file should store telemetry_level?",
        choices=options,
    ).ask()
    if choice == "Create new config file":
        return create_new_config_file()
    return Path(choice).expanduser().resolve()


def write_telemetry_level(path: Path, level: str) -> None:
    """Persist ``telemetry_level`` to a config file.

    Args:
        path: Target ``.codecarbon.config`` path.
        level: Validated tier value.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[codecarbon]\n", encoding="utf-8")
    overwrite_local_config("telemetry_level", level, path=path)


def print_telemetry_status(config_path: Optional[Path] = None) -> None:
    """Print resolved telemetry settings.

    Without ``config_path``, uses the same merged file settings and env overlay
    as ``EmissionsTracker``. With ``config_path``, inspects that file only.

    Args:
        config_path: Optional single config file to inspect.
    """
    if config_path is not None:
        path = config_path.expanduser().resolve()
        if not path.exists():
            print(f"[yellow]Config file not found:[/yellow] {path}")
            print(f"Default tier: {DEFAULT_TELEMETRY_LEVEL.value} (not explicit)")
            return
        file_settings = get_config(path)
        external_conf: dict[str, str] = {}
        source_label = str(path)
    else:
        file_settings = get_config_file_settings()
        external_conf = get_hierarchical_config()
        source_label = "merged ~/.codecarbon.config + ./.codecarbon.config"

    level = resolve_telemetry_level(file_settings)
    explicit = is_telemetry_level_explicit(file_settings, external_conf=external_conf)
    stored = file_settings.get("telemetry_level")
    print(f"Config source: {source_label}")
    print(f"telemetry_level in file(s): {stored!r}")
    print(f"Resolved tier: {level.value}")
    print(f"Explicitly configured: {explicit}")
    if not explicit:
        print(
            "[yellow]Tier 1 minimal telemetry will be sent once per session "
            "until you set telemetry_level.[/yellow]"
        )


def run_telemetry_interactive(config: Optional[Path] = None) -> None:
    """Run the interactive telemetry configuration wizard.

    Args:
        config: Optional fixed config path; otherwise prompt for file choice.
    """
    print("CodeCarbon product telemetry")
    print(
        "Separate from your dashboard experiment (codecarbon config). "
        "Controls optional usage analytics and public leaderboard data.\n"
    )
    path = resolve_config_path(config) if config else None
    if path is None or (config is None and not path.exists()):
        path = pick_config_path_interactive()
    else:
        path = resolve_config_path(config, create=True)

    choices = [
        questionary.Choice("disabled — " + TIER_DESCRIPTIONS["disabled"], "disabled"),
        questionary.Choice("minimal — " + TIER_DESCRIPTIONS["minimal"], "minimal"),
        questionary.Choice(
            "extensive — " + TIER_DESCRIPTIONS["extensive"], "extensive"
        ),
    ]
    try:
        current = get_config(path).get("telemetry_level")
    except FileNotFoundError:
        current = None
    valid_levels = {member.value for member in TelemetryLevel}
    default = current if current in valid_levels else "minimal"
    level = questionary.select(
        "Select telemetry_level:",
        choices=choices,
        default=default,
    ).ask()
    if level is None:
        raise typer.Exit(0)
    level = normalize_telemetry_level(level)
    write_telemetry_level(path, level)
    print(f"[green]Saved[/green] telemetry_level = {level} in {path}")


@telemetry_app.callback(invoke_without_command=True)
def telemetry_entry(
    ctx: typer.Context,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Path to .codecarbon.config (default: local then global).",
        ),
    ] = None,
) -> None:
    """Configure telemetry interactively when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        run_telemetry_interactive(config=config)


@telemetry_app.command("show")
def show(
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Inspect one file only; default matches EmissionsTracker merge.",
        ),
    ] = None,
) -> None:
    """Show the resolved telemetry tier."""
    print_telemetry_status(config_path=config)


@telemetry_app.command("set")
def set_level(
    level: Annotated[
        str,
        typer.Argument(help="Telemetry tier: disabled, minimal, or extensive."),
    ],
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Path to .codecarbon.config (creates ./.codecarbon.config if missing).",
        ),
    ] = None,
) -> None:
    """Write telemetry_level to a config file."""
    path = resolve_config_path(config, create=True)
    normalized = normalize_telemetry_level(level)
    write_telemetry_level(path, normalized)
    print(f"[green]Saved[/green] telemetry_level = {normalized} in {path}")
