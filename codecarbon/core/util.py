from contextlib import contextmanager
from logging import getLogger

logger = getLogger(__name__)


@contextmanager
def suppress(*exceptions):
    try:
        yield
    except exceptions:
        logger.info(exceptions, exc_info=True)
        pass
