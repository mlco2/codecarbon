import configparser

from pathlib import Path


def get_existing_local_exp_id():
    p = Path.cwd().resolve() / ".codecarbon.config"
    if p.exists():
        config = configparser.ConfigParser()
        config.read(str(p))
        if "codecarbon" in config.sections():
            d = dict(config["codecarbon"])
            if "experiment_id" in d:
                return d["experiment_id"]
