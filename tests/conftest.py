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
def _cancel_leaked_scheduler_timers():
    """Stop scheduler threads a test left running.

    PeriodicScheduler re-arms a threading.Timer, so a tracker that is never
    stopped keeps measuring after its test ends. The late measurement lands in
    whatever test is running at the time and corrupts its hardware mocks.
    """
    yield
    for thread in threading.enumerate():
        if isinstance(thread, threading.Timer):
            thread.cancel()
