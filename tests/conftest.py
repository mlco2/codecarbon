"""Shared pytest fixtures for the CodeCarbon test suite."""

import pytest

from codecarbon.core.config import clear_config_cache
from codecarbon.core.hardware_cache import clear_cache as clear_hardware_cache
from codecarbon.core.output_cache import clear_cache as clear_output_cache


@pytest.fixture(autouse=True)
def _reset_process_hardware_cache():
    """Isolate hardware/TDP/GPU probe caches between tests."""
    from codecarbon.core.util import detect_cpu_model

    clear_hardware_cache()
    clear_output_cache()
    clear_config_cache()
    detect_cpu_model.cache_clear()
    yield
    clear_hardware_cache()
    clear_output_cache()
    clear_config_cache()
    detect_cpu_model.cache_clear()
