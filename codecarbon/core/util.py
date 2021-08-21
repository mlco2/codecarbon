import logging
from contextlib import contextmanager

from codecarbon.external.logger import logger


@contextmanager
def suppress(*exceptions):
    try:
        yield
    except exceptions:
        logger.warning("graceful shutdown. Exceptions:")
        logger.warning(
            exceptions if len(exceptions) != 1 else exceptions[0], exc_info=True
        )
        pass


def set_log_level(level: str):
    level = level.upper()
    levels = {
        "CRITICAL",
        "FATAL",
        "ERROR",
        "WARN",
        "WARNING",
        "INFO",
        "DEBUG",
        "NOTSET",
    }
    assert level in levels

    for lev in levels:
        if level == lev:
            logger.setLevel(getattr(logging, level))
            return
    logger.error(f"Unknown log level: {level}")
