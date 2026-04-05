"""Shared pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def isolate_telemetry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid accidental HTTP telemetry during tests from developer/CI env."""
    monkeypatch.setenv("CODECARBON_TELEMETRY", "off")
    monkeypatch.delenv("CODECARBON_TELEMETRY_PROJECT_TOKEN", raising=False)
    monkeypatch.delenv("CODECARBON_TELEMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CODECARBON_TELEMETRY_API_ENDPOINT", raising=False)
