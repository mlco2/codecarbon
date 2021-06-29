import logging
import os

logger = logging.getLogger("codecarbon")
formatter = logging.Formatter(
    "[%(name)s %(levelname)s @ %(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
env_level = os.environ.get("CODECARBON_LOG_LEVEL")
if env_level is None:
    env_level = os.environ.get("codecarbon_log_level")
if env_level is None:
    env_level = "INFO"
logger.setLevel(level=env_level)
