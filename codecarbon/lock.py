"""
Ensures that only one instance of codecarbon is running at a time.
It creates a lock file in /tmp/.codecarbon.lock and removes it on exit.
If the lock file already exists, it exits the program.
"""

import atexit
import errno
import os
import sys

from codecarbon.external.logger import logger

LOCKFILE = "/tmp/.codecarbon.lock"

lock_file_created_by_this_process = False


def acquire_lock():
    """Acquires a lock to ensure only one instance of codecarbon is running."""
    try:
        _create_lock_file()
    except FileExistsError as e:
        logger.error(e)
        logger.error(
            "Error: Another instance of codecarbon is already running. Turn off the other instance to be able to run this one. Exiting."
        )
        sys.exit(1)


def _create_lock_file():
    """Creates a lock file and ensures it's the only instance running."""
    global lock_file_created_by_this_process
    # Attempt to create the lock file
    try:
        with open(LOCKFILE, "x") as _:
            lock_file_created_by_this_process = True
    except FileExistsError:
        logger.debug(
            f"Lock file already exists. Path: {LOCKFILE}. This usually means another instance of codecarbon is running."
        )
        raise


def _remove_lock_file():
    """Removes the lock file on exit."""
    global lock_file_created_by_this_process
    # Only remove the lock file if this process created it
    if lock_file_created_by_this_process:
        try:
            os.remove(LOCKFILE)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


# Register the cleanup function to be called on program exit
atexit.register(_remove_lock_file)
