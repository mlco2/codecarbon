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


@pytest.fixture(autouse=True)
def _isolate_telemetry(monkeypatch):
    """Keep tests off the real telemetry endpoint.

    Telemetry needs no key, so any tracker a test stops would post to
    api.codecarbon.io. Tests that exercise telemetry clear this variable.
    """
    monkeypatch.setenv("CODECARBON_TELEMETRY_LEVEL", "disabled")
    monkeypatch.setattr("codecarbon.core.telemetry.dispatcher._sent", False)
    monkeypatch.setattr("codecarbon.core.telemetry.dispatcher._notice_shown", False)


@pytest.fixture(autouse=True)
def _no_real_browser(monkeypatch):
    """Keep tests headless: never let code under test open a browser tab."""
    monkeypatch.setattr("webbrowser.open", lambda *args, **kwargs: True)
