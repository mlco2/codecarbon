"""Shared pytest fixtures for the CodeCarbon test suite."""

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
