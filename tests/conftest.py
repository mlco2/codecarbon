"""Shared pytest fixtures for the CodeCarbon test suite."""

import threading

import pytest

from codecarbon.core.hardware_cache import clear_cache as clear_hardware_cache


@pytest.fixture(autouse=True)
def _reset_process_hardware_cache():
    """Isolate hardware/TDP/GPU probe caches between tests."""
    # Import probe modules so clear_cache() can reset their lru_cache state.
    import codecarbon.core.cpu  # noqa: F401
    import codecarbon.core.gpu_amd  # noqa: F401
    import codecarbon.core.gpu_nvidia  # noqa: F401
    import codecarbon.core.powermetrics  # noqa: F401
    from codecarbon.core.util import detect_cpu_model

    clear_hardware_cache()
    detect_cpu_model.cache_clear()
    yield
    clear_hardware_cache()
    detect_cpu_model.cache_clear()


@pytest.fixture(autouse=True)
def _no_leaked_scheduler_timers():
    """Fail the test that leaves a scheduler timer running.

    PeriodicScheduler re-arms a threading.Timer, so a tracker that is never
    stopped keeps measuring after its test ends. The late measurement lands in
    whatever test runs next and corrupts its hardware mocks. Cancelling the
    timers silently would hide exactly the leak we want reported.
    """
    yield
    # A cancelled timer stays enumerated until its thread wakes up and exits, so
    # look at the cancellation flag rather than at liveness.
    leaked = [
        t
        for t in threading.enumerate()
        if isinstance(t, threading.Timer) and not t.finished.is_set()
    ]
    for timer in leaked:
        timer.cancel()
    assert not leaked, f"test left scheduler timers running: {leaked}"
