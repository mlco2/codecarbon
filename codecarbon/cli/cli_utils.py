import configparser
from pathlib import Path


def get_api_endpoint():
    p = Path.cwd().resolve() / ".codecarbon.config"
    if p.exists():
        config = configparser.ConfigParser()
        config.read(str(p))
        if "codecarbon" in config.sections():
            d = dict(config["codecarbon"])
            if "api_endpoint" in d:
                return d["api_endpoint"]
    return "https://api.codecarbon.io"


def get_existing_local_exp_id():
    p = Path.cwd().resolve() / ".codecarbon.config"
    if p.exists():
        config = configparser.ConfigParser()
        config.read(str(p))
        if "codecarbon" in config.sections():
            d = dict(config["codecarbon"])
            if "experiment_id" in d:
                return d["experiment_id"]


def write_local_exp_id(exp_id):
    p = Path.cwd().resolve() / ".codecarbon.config"
    config = configparser.ConfigParser()
    if p.exists():
        config.read(str(p))
    if "codecarbon" not in config.sections():
        config.add_section("codecarbon")

    config["codecarbon"]["experiment_id"] = exp_id

    with p.open("w") as f:
        config.write(f)
