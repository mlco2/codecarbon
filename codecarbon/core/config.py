import configparser
import os
from pathlib import Path


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


def parse_gpu_ids(gpu_ids_str):
    """
    Transforms the potential gpu_ids string into a list of int values

    Args:
        gpu_ids_str (str): The config file or environment variable value for `gpu_ids`
        which is read as a string and should be parsed into a list of ints

    Returns:
        list[int]: The list of GPU ids available declared by the user.
            Potentially empty.
    """
    if not isinstance(gpu_ids_str, str):
        return gpu_ids_str

    gpu_ids_str = "".join(c for c in gpu_ids_str if (c.isalnum() or c == ","))
    str_ids = [gpu_id for gpu_id in gpu_ids_str.split(",") if gpu_id]
    return list(map(int, str_ids))


def get_hierarchical_config():
    """
    Get the user-defined codecarbon configuration ConfigParser dictionnary
    (actually a configparser.SectionProxy instance).

    ```
    >>> from codecarbon.core.config import get_hierarchical_config
    >>> conf = get_hierarchical_config()
    >>> print(dict(conf))
    ```

    `conf` works like a regular dict + methods getint(key) getfloat(key)
    and getboolean(key) to automatically parse strings into those types.

    All values (outputs of get(key)) are strings.

    It looks for, and reads, a config file .codecarbon.config in the user's $HOME.
    It then looks for, reads, and updates the previous configuration from a config
    file .codecarbon.config in the current working directory (Path.cwd()).
    Finally it updates the resulting config from any environment variable starting
    with `CODECARBON_` (for instance if `CODECARBON_PROJECT_NAME` is `your-project`
    then the resulting configuration key `project_name` will have value `your-project`)

    Returns:
        configparser.SectionProxy: The final configuration dict parsed from global,
        local and environment configurations. All values are strings.
    """
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
