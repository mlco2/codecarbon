import configparser
from pathlib import Path
import os


def clean_env_key(k: str) -> str:
    """
    Clean up an environment variable key: remove starting
    CODECARBON_ and to lower case.

    eg: "CODECARBON_PROJECT_NAME" -> "project_name"

    Args:
        k (str): Environment variable key

    Returns:
        str: Cleaned str
    """
    assert isinstance(k, str)
    return k.replace("CODECARBON_", "").lower()


def parse_env_config() -> dict:
    """
    Get all environment variables starting with "CODECARBON_" mapped
    to their values in a dict

    eg: "CODECARBON_PROJECT_NAME=deeplearning" -> {"project_name": "deeplearning"}

    Returns:
        dict: existing relevant environment variables mapped into a dict
    """
    return {
        "codecarbon": {
            clean_env_key(k): v
            for k, v in os.environ.items()
            if k.startswith("CODECARBON_")
        }
    }


def get_hierarchical_config():
    cwd = Path.cwd()
    global_config = configparser.ConfigParser()
    local_config = configparser.ConfigParser()
    env_config = configparser.ConfigParser()
    full_config = configparser.ConfigParser()

    global_config.read(Path("~/.codecarbon.config").expanduser().resolve())
    local_config.read((cwd / ".codecarbon.config").expanduser().resolve())
    env_config.read_dict(parse_env_config())

    full_config.read_dict(global_config)
    full_config.read_dict(local_config)
    full_config.read_dict(env_config)
    config = full_config["codecarbon"]
    return config
