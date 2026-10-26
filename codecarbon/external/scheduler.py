import math
import time
from threading import Event, Lock, Thread, current_thread

from codecarbon.external.logger import logger

# Longest stop() waits for the in-flight call, a guess at "a measurement should
# never take longer than this", so a wedged one cannot hang the caller for long.
STOP_JOIN_TIMEOUT_SECONDS = 5.0


class PeriodicScheduler:
    """
    Run ``function`` every ``interval`` seconds on a single daemon thread.

    The deadline is absolute, so the cadence does not drift with the time the
    function itself takes. A tick that overruns its slot is skipped rather than
    queued, so the function is never re-entered.
    """

    def __init__(self, interval, function, *args, **kwargs):
        """
        ::interval:: in seconds, the delay between two calls to function.
        ::function:: the function to call.
        ::args:: args to pass to the function.
        ::kwargs:: kwargs to pass to the function.
        """
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._lock = Lock()
        self._thread = None
        self._stop_event = None

    @property
    def _stopped(self):
        return self._stop_event is None or self._stop_event.is_set()

    def start(self):
        """
        Start the scheduler. Calling it on a running scheduler is a no-op.
        If a previous run is still finishing its callback (a timed-out
        stop()), the new loop waits for it before its first tick, so the
        function is never run concurrently and the restart is not lost.
        """
        with self._lock:
            if self._thread is not None and not self._stopped:
                return
            self._stop_event = Event()
            self._thread = Thread(
                target=self._loop,
                args=(self._stop_event, self._thread),
                daemon=True,
                name=f"codecarbon-{getattr(self.function, '__name__', 'scheduler')}",
            )
            self._thread.start()

    def _loop(self, stop_event, previous=None):
        if previous is not None:
            previous.join()
        next_call = time.monotonic() + self.interval
        while not stop_event.wait(max(0.0, next_call - time.monotonic())):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception:  # noqa: BLE001 - must not kill the only thread
                logger.error("Scheduled measurement failed", exc_info=True)
            next_call += self.interval
            overrun = time.monotonic() - next_call
            if overrun > 0 and self.interval > 0:
                # Skip the slots the call overran: no burst of catch-up ticks,
                # and no back-to-back call either.
                next_call += math.ceil(overrun / self.interval) * self.interval

    def stop(self):
        """
        Stop the scheduler and wait for the in-flight call to return, at most
        min(interval, STOP_JOIN_TIMEOUT_SECONDS) seconds.
        """
        with self._lock:
            if self._stop_event is not None:
                self._stop_event.set()
            thread = self._thread
        if thread is None or thread is current_thread():
            # Called from the callback itself: it is still running, so keep
            # the reference for the next start() to wait on.
            return
        thread.join(min(self.interval, STOP_JOIN_TIMEOUT_SECONDS))
        if thread.is_alive():
            # Keep the reference so the next start() waits for it.
            logger.warning(
                "Scheduled measurement still running after stop(); it will"
                " finish in the background"
            )
        else:
            with self._lock:
                if self._thread is thread:
                    self._thread = None
