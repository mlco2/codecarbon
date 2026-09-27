"""Integration tests for telemetry against a running local carbonserver API."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from codecarbon.core.telemetry.client import post_private  # noqa: E402
from codecarbon.core.telemetry.collect import build_payload  # noqa: E402
from codecarbon.core.telemetry.schemas import TelemetryLevel  # noqa: E402
from codecarbon.core.telemetry.settings import TelemetrySettings  # noqa: E402
from codecarbon.output_methods.emissions_data import EmissionsData  # noqa: E402

URL = os.getenv("CODECARBON_API_URL")
if URL is None:
    pytest.exit("CODECARBON_API_URL is not defined (e.g. http://localhost:8008)")


def _local_settings() -> TelemetrySettings:
    return TelemetrySettings.resolve(
        external_conf={
            "telemetry_level": "minimal",
            "telemetry_api_url": URL.rstrip("/"),
        }
    )


def _sample_emissions() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-01-01T00:00:00",
        project_name="telemetry-local",
        run_id="local-run",
        experiment_id="e",
        duration=10.0,
        emissions=0.001,
        emissions_rate=0.0001,
        cpu_power=0.0,
        gpu_power=0.0,
        ram_power=0.0,
        cpu_energy=0.0,
        gpu_energy=0.0,
        ram_energy=0.0,
        energy_consumed=0.01,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="idf",
        cloud_provider="",
        cloud_region="",
        os="Linux",
        python_version="3.12",
        codecarbon_version="3.2.8",
        cpu_count=4,
        cpu_model="test-cpu",
        gpu_count=0,
        gpu_model="",
        longitude=0.0,
        latitude=0.0,
        ram_total_size=16.0,
        tracking_mode="process",
    )


def test_local_api_is_up():
    response = requests.get(URL.rstrip("/") + "/", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_local_telemetry_post_accepts_sdk_payload():
    settings = _local_settings()
    tracker = SimpleNamespace(
        _conf={
            "os": "Linux-5.10.0-x86_64",
            "codecarbon_version": "3.2.8",
            "cpu_count": 4,
            "python_version": "3.12",
            "tracking_mode": "process",
        },
    )
    payload = build_payload(tracker, _sample_emissions(), level=TelemetryLevel.minimal)
    assert post_private(settings, payload) is True
