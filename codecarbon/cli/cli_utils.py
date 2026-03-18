import configparser
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm


def get_config(path: Optional[Path] = None):
    p = path or Path.cwd().resolve() / ".codecarbon.config"

    if p.exists():
        config = configparser.ConfigParser()
        config.read(str(p))
        if "codecarbon" in config.sections():
            d = dict(config["codecarbon"])
            return d

    else:
        raise FileNotFoundError(
            "No .codecarbon.config file found in the current directory."
        )


def get_api_endpoint(path: Optional[Path] = None):
    p = path or Path.cwd().resolve() / ".codecarbon.config"
    if p.exists():
        config = configparser.ConfigParser()
        config.read(str(p))
        if "codecarbon" in config.sections():
            d = dict(config["codecarbon"])
            if "api_endpoint" in d:
                return d["api_endpoint"]
            else:
                with p.open("a") as f:
                    f.write("api_endpoint=https://api.codecarbon.io\n")
    return "https://api.codecarbon.io"


def get_existing_local_exp_id(path: Optional[Path] = None):
    p = path or Path.cwd().resolve() / ".codecarbon.config"
    if p.exists():
        existing_path = p
    else:
        existing_path = Path("~/.codecarbon.config").expanduser()
    return _get_local_exp_id(existing_path)


def _get_local_exp_id(p: Optional[Path] = None):
    config = configparser.ConfigParser()
    config.read(str(p))
    if "codecarbon" in config.sections():
        d = dict(config["codecarbon"])
        if "experiment_id" in d:
            return d["experiment_id"]


def write_local_exp_id(exp_id, path: Optional[Path] = None):
    p = path or Path.cwd().resolve() / ".codecarbon.config"

    config = configparser.ConfigParser()
    if p.exists():
        config.read(str(p))
    if "codecarbon" not in config.sections():
        config.add_section("codecarbon")

    config["codecarbon"]["experiment_id"] = exp_id

    with p.open("w") as f:
        config.write(f)


def overwrite_local_config(config_name, value, path: Optional[Path] = None):
    p = path or Path.cwd().resolve() / ".codecarbon.config"

    config = configparser.ConfigParser()
    if p.exists():
        config.read(str(p))
    if "codecarbon" not in config.sections():
        config.add_section("codecarbon")

    config["codecarbon"][config_name] = value
    with p.open("w") as f:
        config.write(f)


def create_new_config_file():
    typer.echo("Creating new config file")
    file_path = typer.prompt(
        "Where do you want to put your config file ?",
        type=str,
        default="~/.codecarbon.config",
    )
    if file_path[0] == "~":
        file_path = Path.home() / file_path[2:]
    else:
        file_path = Path(file_path)

    if not file_path.parent.exists():
        create = Confirm.ask(
            "Parent folder does not exist do you want to create it (and parents) ?"
        )
        if create:
            file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.touch()
    with open(file_path, "w") as f:
        f.write("[codecarbon]\n")
    typer.echo(f"Config file created at {file_path}")
    return file_path


def save_telemetry_config_to_file(
    tier: str = None,
    project_token: str = None,
    api_endpoint: str = None,
    path: Path = None
) -> None:
    """
    Save telemetry configuration as JSON in the existing config file.
    
    Args:
        tier: Telemetry tier (off, internal, public)
        project_token: Project token for Tier 2
        api_endpoint: API endpoint for telemetry
        path: Path to config file (defaults to ~/.codecarbon.config)
    """
    import json
    
    p = path or Path.home() / ".codecarbon.config"
    
    # Read existing config or create new
    config = configparser.ConfigParser()
    if p.exists():
        config.read(str(p))
    
    if "codecarbon" not in config.sections():
        config.add_section("codecarbon")
    
    # Build JSON config for telemetry
    telemetry_config = {}
    if tier:
        telemetry_config["telemetry_tier"] = tier
    if project_token:
        telemetry_config["telemetry_project_token"] = project_token
    if api_endpoint:
        telemetry_config["telemetry_api_endpoint"] = api_endpoint
    
    # Save as JSON string
    if telemetry_config:
        config["codecarbon"]["telemetry"] = json.dumps(telemetry_config)
    
    with p.open("w") as f:
        config.write(f)
    logger.info(f"Telemetry config saved to {p}")


def load_telemetry_config_from_file(path: Path = None) -> dict:
    """
    Load telemetry configuration from the existing config file.
    
    Args:
        path: Path to config file (defaults to ~/.codecarbon.config)
        
    Returns:
        Dictionary with telemetry configuration
    """
    import json
    
    p = path or Path.home() / ".codecarbon.config"
    
    if not p.exists():
        return {}
    
    config = configparser.ConfigParser()
    config.read(str(p))
    
    if "codecarbon" not in config.sections():
        return {}
    
    telemetry_str = config["codecarbon"].get("telemetry")
    if telemetry_str:
        try:
            return json.loads(telemetry_str)
        except json.JSONDecodeError:
            return {}
    
    return {}
