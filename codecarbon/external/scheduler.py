from threading import Lock, Timer

from codecarbon.external.logger import logger


class PeriodicScheduler(object):
    """
    A periodic task running in threading.Timers
    From https://stackoverflow.com/a/18906292/14541668
    """

    def __init__(self, interval, function, *args, **kwargs):
        """
        Init the scheduler. You have to call with autostart=True
        if ou want to start it without having to calling start().
        ::interval:: interval in seconds to run the function.
        ::function:: function to run.
        ::args:: args to pass to the function.
        ::kwargs:: kwargs to pass to the function.
        """
        self._lock = Lock()
        self._timer = None
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self._stopped = True
        if kwargs.pop("autostart", True):
            self.start()
            msg = f"PeriodicScheduler is ready to run {self.function} in {self.interval} seconds."
        else:
            msg += " You have to call .start() before."
        logger.debug(msg)

    def start(self, from_run=False):
        """
        Start the scheduler.
        ::from_run:: For internal purposes to allow re-scheduling
        Please do not use from_run=True until you know what you do !
        """
        # logger.debug(f"In PeriodicScheduler.start()")
        self._lock.acquire()
        if from_run or self._stopped:
            self._stopped = False
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
        self._lock.release()

    def _run(self):
        # logger.debug(f"In PeriodicScheduler._run()")
        self.start(from_run=True)
        # logger.debug(f"PeriodicScheduler run {self.function}")
        self.function(*self.args, **self.kwargs)

    def stop(self):
        """
        Stop the scheduler.
        """
        self._lock.acquire()
        self._stopped = True
        self._timer.cancel()
        self._lock.release()
