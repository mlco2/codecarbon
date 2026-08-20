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
        # Reentrant: _handle_exit -> release() can fire on a thread already holding it.
        self._thread_lock = threading.RLock()
        # Previous signal handlers, restored on release().
        self._previous_handlers = {}

    def _handle_exit(self, signum, frame):
        """Releases the lock, then delegates to the handler we replaced."""
        logger.debug(f"Signal {signum} received. Releasing lock.")
        previous = self._previous_handlers.get(signum, signal.SIG_DFL)
        self.release()  # also restores the previous handlers
        if callable(previous):
            return previous(signum, frame)
        if previous == signal.SIG_DFL:
            os.kill(os.getpid(), signum)

    def acquire(self):
        """Creates a lock file and ensures it's the only instance running."""
        with self._thread_lock:
            # Attempt to create the lock file
            try:
                with open(LOCKFILE, "x") as _:
                    logger.debug(f"Lock file created. Path: {LOCKFILE}")
                    self._has_created_lock = True
                # Only now that we own the lock file: a failed acquire() must not
                # leave the host application's handlers hijacked for good, since
                # release() is never reached on that path.
                if threading.current_thread() is threading.main_thread():
                    for sig in (signal.SIGINT, signal.SIGTERM):
                        self._previous_handlers[sig] = signal.signal(
                            sig, self._handle_exit
                        )
            except FileExistsError:
                logger.debug(
                    f"Lock file {LOCKFILE} already exists. This usually means another instance of codecarbon is running. You can safely delete it if you want or use allow_multiple_runs parameter to always bypass it."
                )
                raise

    def release(self):
        """Removes the lock file and restores the signal handlers we replaced."""
        with self._thread_lock:
            logger.debug("Removing the lock")
            while self._previous_handlers:
                sig, handler = self._previous_handlers.popitem()
                # Only restore if nobody installed another handler after us.
                if signal.getsignal(sig) == self._handle_exit:
                    signal.signal(sig, handler)
            atexit.unregister(self.release)
            try:
                # Remove the lock file only if it was created by this instance
                if self._has_created_lock:
                    self._has_created_lock = False
                    os.remove(LOCKFILE)
            except OSError as e:
                logger.debug(f"Error: {e}")
                if e.errno != errno.ENOENT:
                    raise
