import configparser
import os
from pathlib import Path
from typing import List, Union

from codecarbon.external.logger import logger


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
    return k.lower().replace("codecarbon_", "", 1)


def parse_env_config() -> dict:
    """
    Get all environment variables starting with "CODECARBON_" (also in lower caps)
    mapped to their values in a dict

    eg:
        * "CODECARBON_PROJECT_NAME=DeepLearning" -> {"project_name": "DeepLearning"}
        * "codecarbon_project_name=DeepLearning" -> {"project_name": "DeepLearning"}

    Returns:
        dict: existing relevant environment variables mapped into a dict
    """
    return {
        "codecarbon": {
            clean_env_key(k): v
            for k, v in os.environ.items()
            if k.lower().startswith("codecarbon_")
        }
    }


def parse_gpu_ids(gpu_ids: Union[str, List[int]]) -> List[str]:
    """
    Transforms the potential gpu_ids into a list of string id values.


    Args:
        gpu_ids: The config file or environment variable value for `gpu_ids`

    Returns:
        list[str]: The list of GPU ids available.
            Potentially empty.
    """
    if isinstance(gpu_ids, str):
        # Allow '-' in id strings since UUIDs may include them.
        gpu_ids = "".join(c for c in gpu_ids if (c.isalnum() or c in ("-", ",")))
        str_ids = [gpu_id for gpu_id in gpu_ids.split(",") if gpu_id]
        return str_ids

    elif isinstance(gpu_ids, list) and all(
        isinstance(gpu_id, int) for gpu_id in gpu_ids
    ):
        return list(map(str, gpu_ids))

    else:
        logger.warning(
            "Invalid gpu_ids format. Expected a string or a list of ints/strings."
        )


def get_hierarchical_config():
    """
    Get the user-defined codecarbon configuration ConfigParser dictionnary
    (actually a configparser.SectionProxy instance).

    ```
    >>> from codecarbon.core.config import get_hierarchical_config
    >>> conf = get_hierarchical_config()
    >>> print(conf)
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
        dict: The final configuration dict parsed from global,
        local and environment configurations. **All values are strings**.
    """

    config = configparser.ConfigParser()

    cwd = Path.cwd()
    home = Path.home()
    global_path = str((home / ".codecarbon.config").expanduser().resolve())
    local_path = str((cwd / ".codecarbon.config").expanduser().resolve())
    if Path(global_path).exists():
        logger.info(
            f"Codecarbon is taking the configuration from global file: {global_path}"
        )
        if Path(local_path).exists():
            logger.info(f"Some variables are overriden by the local file: {local_path}")
    elif Path(local_path).exists():
        logger.info(
            f"Codecarbon is taking the configuration from the local file {local_path}"
        )

    config.read([global_path, local_path])
    config.read_dict(parse_env_config())

    return dict(config["codecarbon"])
