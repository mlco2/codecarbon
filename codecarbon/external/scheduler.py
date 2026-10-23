import time
from threading import Event, Thread, current_thread

from codecarbon.external.logger import logger


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
        self._thread = None
        self._stop_event = None

    @property
    def _stopped(self):
        return self._stop_event is None or self._stop_event.is_set()

    def _join_timeout(self, timeout):
        # ponytail: 5s cap is a guess at "a measurement should never take
        # longer than this"; make it configurable if a slow hardware
        # backend ever needs more.
        return min(self.interval, 5.0) if timeout is None else timeout

    def start(self):
        """
        Start the scheduler. Calling it on a running scheduler is a no-op.
        If a previous run is still finishing its callback (a timed-out
        stop()), wait for it; if it is still busy, refuse to start a second
        loop so the function is never run concurrently.
        """
        if self._thread is not None:
            if not self._stopped:
                return
            self._thread.join(self._join_timeout(None))
            if self._thread.is_alive():
                logger.warning(
                    "Previous scheduled measurement is still running;"
                    " not starting a second loop"
                )
                return
        self._stop_event = Event()
        self._thread = Thread(
            target=self._loop,
            args=(self._stop_event,),
            daemon=True,
            name=f"codecarbon-{getattr(self.function, '__name__', 'scheduler')}",
        )
        self._thread.start()

    def _loop(self, stop_event):
        next_call = time.monotonic() + self.interval
        while not stop_event.wait(max(0.0, next_call - time.monotonic())):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception:  # noqa: BLE001 - must not kill the only thread
                logger.error("Scheduled measurement failed", exc_info=True)
            # Absolute deadline, but never a burst of catch-up ticks.
            next_call = max(next_call + self.interval, time.monotonic())

    def stop(self, timeout=None):
        """
        Stop the scheduler and wait for the in-flight call to return.
        ::timeout:: seconds to wait for the running function, bounded by
        default so a wedged measurement cannot hang the caller for long.
        """
        if self._stop_event is not None:
            self._stop_event.set()
        thread = self._thread
        if thread is None or thread is current_thread():
            self._thread = None
            return
        thread.join(self._join_timeout(timeout))
        if thread.is_alive():
            # Keep the reference so start() will not launch a second loop.
            logger.warning(
                "Scheduled measurement still running after stop(); it will"
                " finish in the background and may overlap the next one"
            )
        else:
            self._thread = None
