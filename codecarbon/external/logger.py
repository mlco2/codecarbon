import logging
import os
from typing import Optional


def set_logger_format(custom_preamble: Optional[str] = ""):
    logger = logging.getLogger("codecarbon")
    format = "[%(name)s %(levelname)s @ %(asctime)s]"
    if custom_preamble:
        format += f"[{custom_preamble}]"
    format += " %(message)s"
    formatter = logging.Formatter(format, datefmt="%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)


def set_logger_level(level: Optional[str] = None):
    if level is None:
        lower_envs = {k.lower(): v for k, v in os.environ.items()}
        level = lower_envs.get("codecarbon_log_level", "INFO")

    logger = logging.getLogger("codecarbon")

    if isinstance(level, int):
        known_levels_int = {0, 10, 20, 30, 40, 50}
        if level not in known_levels_int:
            logger.error(f"Unknown int log level: {level}. Doing nothing.")
            return
        logger.setLevel(level)
        return

    if isinstance(level, str):
        level = level.upper()
        known_levels_str = {
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARN",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        }

        if level not in known_levels_str:
            logger.error(f"Unknown str log level: {level}. Doing nothing.")
            return
        logger.setLevel(level)
        return

    logger.error(f"Unknown log level: {level}. Doing nothing.")


set_logger_format()
set_logger_level()

logger = logging.getLogger("codecarbon")
logger.propagate = False
