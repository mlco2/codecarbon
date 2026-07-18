"""Integration tests for telemetry against a running local carbonserver API."""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from codecarbon.core.telemetry.client import post_private, post_public_summary
from codecarbon.core.telemetry.collect import TelemetryContext, build_payload
from codecarbon.core.telemetry.defaults import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
)
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.output_methods.emissions_data import EmissionsData

URL = os.getenv("CODECARBON_API_URL")
if URL is None:
    pytest.exit("CODECARBON_API_URL is not defined (e.g. http://localhost:8008)")


def _api_url(path: str) -> str:
    base = URL.rstrip("/")
    if not base.endswith("/api"):
        base = f"{base}/api"
    return f"{base}{path}"


def _local_settings() -> TelemetrySettings:
    return TelemetrySettings.resolve(
        external_conf={
            "telemetry_level": "extensive",
            "telemetry_api_url": URL.rstrip("/"),
            "telemetry_api_key": DEFAULT_TELEMETRY_API_KEY,
            "telemetry_experiment_id": DEFAULT_TELEMETRY_EXPERIMENT_ID,
        }
    )


def _sample_emissions() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-01-01T00:00:00",
        project_name="telemetry-local",
        run_id="local-run",
        experiment_id=DEFAULT_TELEMETRY_EXPERIMENT_ID,
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
    payload = build_payload(
        TelemetryContext(
            conf={
                "os": "Linux-5.10.0-x86_64",
                "codecarbon_version": "3.2.8",
                "cpu_count": 4,
                "python_version": "3.12",
                "tracking_mode": "process",
            },
            emissions=_sample_emissions(),
            hardware=[],
            resource_tracker=None,
            output_methods=[],
            tasks={},
            measure_power_secs=15,
            integration="library",
        ),
        level=TelemetryLevel.minimal,
    )
    assert post_private(settings, payload) is True


def test_local_extensive_run_and_emission_flow():
    settings = _local_settings()
    run_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment_id": settings.experiment_id,
        "os": "Linux",
        "python_version": "3.12",
        "codecarbon_version": "3.2.8",
        "cpu_count": 4,
        "tracking_mode": "process",
    }
    run_response = requests.post(
        _api_url("/runs"),
        json=run_payload,
        headers={"x-api-token": settings.api_key},
        timeout=10,
    )
    assert run_response.status_code == 201, run_response.text
    run_id = run_response.json()["id"]

    emission_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "duration": 10,
        "emissions_sum": 0.001,
        "emissions_rate": 0.0001,
        "cpu_power": 0.0,
        "gpu_power": 0.0,
        "ram_power": 0.0,
        "cpu_energy": 0.0,
        "gpu_energy": 0.0,
        "ram_energy": 0.0,
        "energy_consumed": 0.01,
        "wue": 0,
    }
    emission_response = requests.post(
        _api_url("/emissions"),
        json=emission_payload,
        headers={"x-api-token": settings.api_key},
        timeout=10,
    )
    assert emission_response.status_code == 201, emission_response.text
    assert uuid.UUID(emission_response.json())


def test_local_post_public_summary_helper():
    settings = _local_settings()
    assert (
        post_public_summary(settings, {"os": "Linux", "tracking_mode": "process"}, _sample_emissions())
        is True
    )
