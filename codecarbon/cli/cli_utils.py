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
