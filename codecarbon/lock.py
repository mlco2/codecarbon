"""
Ensures that only one instance of codecarbon is running at a time.
It creates a lock file in /tmp/.codecarbon.lock and removes it on exit.
If the lock file already exists, it exits the program.
"""

import errno
import os
import tempfile

from codecarbon.external.logger import logger

# We use tempfile.gettempdir() to get the system's temporary directory (linux: /tmp, windows: C:\Users\username\AppData\Local\Temp)
LOCKFILE = os.path.join(tempfile.gettempdir(), ".codecarbon.lock")


class Lock:
    """A lock to ensure only one instance of codecarbon is running."""

    def __init__(self):
        self._has_created_lock = False

    def acquire(self):
        """Creates a lock file and ensures it's the only instance running."""
        # Attempt to create the lock file
        try:
            with open(LOCKFILE, "x") as _:
                logger.debug(f"Lock file created. Path: {LOCKFILE}")
                self._has_created_lock = True
        except FileExistsError:
            logger.debug(
                f"Lock file already exists. Path: {LOCKFILE}. This usually means another instance of codecarbon is running."
            )
            raise

    def release(self):
        """Removes the lock file on exit."""
        logger.debug("Removing the lock")
        try:
            # Remove the lock file only if it was created by this instance
            if self._has_created_lock:
                os.remove(LOCKFILE)
        except OSError as e:
            logger.error("Error:", e)
            if e.errno != errno.ENOENT:
                raise
