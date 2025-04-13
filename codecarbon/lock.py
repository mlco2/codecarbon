"""
Ensures that only one instance of codecarbon is running at a time.
It creates a lock file in /tmp/.codecarbon.lock and removes it on exit.
If the lock file already exists, it exits the program.
"""

import atexit
import errno
import os
import signal
import tempfile
import threading

from codecarbon.external.logger import logger

# We use tempfile.gettempdir() to get the system's temporary directory (linux: /tmp, windows: C:\Users\username\AppData\Local\Temp)
LOCKFILE = os.path.join(tempfile.gettempdir(), ".codecarbon.lock")


class Lock:
    """A lock to ensure only one instance of codecarbon is running."""

    def __init__(self):
        self._has_created_lock = False
        self.lockfile_path = LOCKFILE
        atexit.register(
            self.release
        )  # Ensure release() is called on unexpected exit of the user's python code
        # If there is more than one thread add a lock
        self._thread_lock = threading.Lock()
        # If the current thread is the main thread, register signal handlers
        if threading.current_thread() is threading.main_thread():
            # Register signal handlers to ensure lock release on interruption
            signal.signal(signal.SIGINT, self._handle_exit)  # Ctrl+C
            signal.signal(signal.SIGTERM, self._handle_exit)  # Termination signal

    def _handle_exit(self, signum, frame):
        """Ensures the lock file is removed when the script is interrupted."""
        logger.debug(f"Signal {signum} received. Releasing lock and exiting.")
        self.release()
        raise SystemExit(1)  # Exit gracefully to prevent further execution

    def acquire(self):
        """Creates a lock file and ensures it's the only instance running."""
        with self._thread_lock:
            # Attempt to create the lock file
            try:
                with open(LOCKFILE, "x") as _:
                    logger.debug(f"Lock file created. Path: {LOCKFILE}")
                    self._has_created_lock = True
            except FileExistsError:
                logger.debug(
                    f"Lock file {LOCKFILE} already exists. This usually means another instance of codecarbon is running. You can safely delete it if you want or use allow_multiple_runs parameter to always bypass it."
                )
                raise

    def release(self):
        """Removes the lock file on exit."""
        with self._thread_lock:
            logger.debug("Removing the lock")
            try:
                # Remove the lock file only if it was created by this instance
                if self._has_created_lock:
                    os.remove(LOCKFILE)
            except OSError as e:
                logger.debug(f"Error: {e}")
                if e.errno != errno.ENOENT:
                    raise
