import logging
from contextlib import contextmanager

logger = logging.getLogger("codecarbon")


@contextmanager
def suppress(*exceptions):
    try:
        yield
    except exceptions:
        logger.warning("CODECARBON: graceful shutdown. Exceptions:")
        logger.warning(
            exceptions if len(exceptions) != 1 else exceptions[0], exc_info=True
        )
        logger.warning("CODECARBON: stopping.")
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
