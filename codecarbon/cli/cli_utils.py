import configparser
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm

from codecarbon.core.config import get_hierarchical_config


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


def get_existing_exp_id() -> Optional[str]:
    """
    Return experiment_id resolved from the same hierarchical config strategy
    used by EmissionsTracker (global file, local file, then CODECARBON_* env).
    """
    try:
        conf = get_hierarchical_config()
    except KeyError:
        return None
    return conf.get("experiment_id")


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
