import builtins
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from codecarbon.input import DataSource


# don't use vanilla unittest.mock.mock_openfor <3.7 compatibility
# https://stackoverflow.com/a/41656192/3867406
def mock_open(*args, **kargs):
    f_open = unittest.mock.mock_open(*args, **kargs)
    f_open.return_value.__iter__ = lambda self: iter(self.readline, "")
    return f_open


OPEN = builtins.open


def get_test_data_source() -> DataSource:
    return DataSource()


def get_custom_mock_open(global_conf_str, local_conf_str) -> callable:
    def mocked_open():
        def conditional_open_func(path, *args, **kwargs):
            p = Path(path).expanduser().resolve()
            if p.name == ".codecarbon.config":
                if p.parent == Path.home():
                    return mock_open(read_data=global_conf_str)()
                return mock_open(read_data=local_conf_str)()
            return OPEN(path, *args, **kwargs)

        return conditional_open_func

    return mocked_open


class FakeClock:
    """
    Fake time for ``PeriodicScheduler.clock``: the loop only moves when the
    test calls advance(), so tests assert on exact ticks instead of sleeping.
    """

    def __init__(self):
        self.now = 0.0
        self._cond = threading.Condition()
        self._parked = set()

    def monotonic(self):
        with self._cond:
            return self.now

    def sleep(self, seconds):
        """Let a scheduled function take ``seconds`` of fake time."""
        with self._cond:
            self.now += seconds

    def wait(self, event, timeout):
        me = threading.current_thread()
        with self._cond:
            deadline = self.now + timeout
            while not event.is_set() and self.now < deadline:
                self._parked.add(me)
                self._cond.notify_all()
                # stop() sets the event without notifying us, so poll it.
                self._cond.wait(0.001)
            self._parked.discard(me)
            self._cond.notify_all()
            return event.is_set()

    def wait_parked(self, timeout=2.0):
        """True once a loop is waiting for its next deadline."""
        with self._cond:
            return self._cond.wait_for(lambda: self._parked, timeout)

    def advance(self, seconds, settle=True):
        """
        Move time forward once a loop is waiting. With ``settle``, return only
        when the loop has run what was due and is waiting again.
        """
        assert self.wait_parked(), "no scheduler loop is waiting"
        with self._cond:
            self.now += seconds
            self._parked.clear()
            self._cond.notify_all()
        if settle:
            assert self.wait_parked(), "the scheduler loop did not settle"


def join_telemetry(tracker, timeout: float = 10.0) -> None:
    """Wait for the background telemetry send that ``stop()`` fired, if any."""
    thread = getattr(getattr(tracker, "_telemetry", None), "_thread", None)
    if thread is not None:
        thread.join(timeout)


@contextmanager
def hanging_endpoint():
    """Yield a URL whose TCP connections are accepted but never answered."""
    import socket

    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(8)  # backlog completes the handshake; we never accept()
    try:
        yield "http://{}:{}".format(*server.getsockname())
    finally:
        server.close()


@contextmanager
def ensure_telemetry_run_duration(min_seconds: float = 10.0):
    """Force tracker stop emissions duration above telemetry's 1s minimum."""
    from codecarbon.emissions_tracker import BaseEmissionsTracker

    original_prepare = BaseEmissionsTracker._prepare_emissions_data

    def prepare_with_min_duration(self):
        data = original_prepare(self)
        if data is not None and (data.duration is None or data.duration < min_seconds):
            data.duration = min_seconds
        return data

    with patch.object(
        BaseEmissionsTracker, "_prepare_emissions_data", prepare_with_min_duration
    ):
        yield
