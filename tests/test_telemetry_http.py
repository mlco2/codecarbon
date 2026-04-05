"""Tests for HTTP-based telemetry (POST /telemetry and POST /emissions)."""

import json
from pathlib import Path

import pytest
import responses

import codecarbon.core.telemetry.service as telemetry_service_module
from codecarbon.core.telemetry import config as telemetry_config_module
from codecarbon.core.telemetry.config import (
    TELEMETRY_API_ENDPOINT_ENV_VAR,
    TELEMETRY_API_KEY_ENV_VAR,
    TELEMETRY_ENV_VAR,
)
from codecarbon.core.telemetry.service import TelemetryService, init_telemetry


@pytest.fixture
def reset_telemetry_service():
    telemetry_service_module._telemetry_service = None
    TelemetryService._instance = None
    yield
    telemetry_service_module._telemetry_service = None
    TelemetryService._instance = None


@pytest.fixture
def telemetry_internal_env(monkeypatch, reset_telemetry_service):
    monkeypatch.setenv(TELEMETRY_ENV_VAR, "internal")
    monkeypatch.setenv(TELEMETRY_API_ENDPOINT_ENV_VAR, "https://telemetry.test")


@pytest.fixture
def telemetry_public_env(monkeypatch, reset_telemetry_service):
    monkeypatch.delenv("CODECARBON_API_KEY", raising=False)
    monkeypatch.setenv(TELEMETRY_ENV_VAR, "public")
    monkeypatch.setenv(TELEMETRY_API_KEY_ENV_VAR, "test-project-token")
    monkeypatch.setenv(TELEMETRY_API_ENDPOINT_ENV_VAR, "https://telemetry.test")
    monkeypatch.setattr(
        telemetry_config_module,
        "DEFAULT_PUBLIC_TELEMETRY_TOKEN",
        "",
    )
    monkeypatch.setattr(
        "codecarbon.cli.cli_utils.load_telemetry_config_from_file",
        lambda path=None: {},
    )
    monkeypatch.setattr(
        "codecarbon.core.telemetry.config.load_telemetry_preference",
        lambda: None,
    )
    monkeypatch.setattr(
        telemetry_config_module,
        "get_telemetry_preference_file",
        lambda: Path("/nonexistent/codecarbon-telemetry-pref.txt"),
    )


@responses.activate
def test_internal_posts_telemetry_without_emission_keys(
    telemetry_internal_env,
):
    responses.add(
        responses.POST,
        "https://telemetry.test/telemetry",
        json={},
        status=201,
    )

    init_telemetry()
    svc = telemetry_service_module.get_telemetry_service()
    ok = svc.collect_and_export(cpu_count=4, cpu_model="TestCPU", gpu_count=0)

    assert ok is True
    assert len(responses.calls) == 1
    body = json.loads(responses.calls[0].request.body)
    assert body.get("telemetry_tier") == "internal"
    assert "total_emissions_kg" not in body
    assert body.get("cpu_count") == 4
    assert body.get("cpu_model") == "TestCPU"


@responses.activate
def test_public_posts_telemetry_and_emissions(telemetry_public_env):
    responses.add(
        responses.POST,
        "https://telemetry.test/telemetry",
        json={},
        status=201,
    )
    responses.add(
        responses.POST,
        "https://telemetry.test/emissions",
        json={},
        status=200,
    )

    init_telemetry()
    svc = telemetry_service_module.get_telemetry_service()

    assert svc.collect_and_export(cpu_count=2, cpu_model="x")
    assert svc.export_emissions(
        total_emissions_kg=0.01,
        emissions_rate_kg_per_sec=1e-4,
        energy_consumed_kwh=0.5,
        cpu_energy_kwh=0.3,
        gpu_energy_kwh=0.1,
        ram_energy_kwh=0.1,
        duration_seconds=60.0,
        cpu_utilization_avg=12.5,
        gpu_utilization_avg=0.0,
        ram_utilization_avg=40.0,
    )

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url.endswith("/telemetry")
    tel_body = json.loads(responses.calls[0].request.body)
    assert tel_body.get("telemetry_tier") == "public"

    em_req = responses.calls[1].request
    assert em_req.url.endswith("/emissions")
    assert em_req.headers.get("x-api-token") == "test-project-token"
    em_body = json.loads(em_req.body)
    assert em_body["total_emissions_kg"] == 0.01
    assert em_body["duration_seconds"] == 60.0


@responses.activate
def test_public_emissions_skipped_short_duration(telemetry_public_env):
    responses.add(
        responses.POST,
        "https://telemetry.test/telemetry",
        json={},
        status=201,
    )

    init_telemetry()
    svc = telemetry_service_module.get_telemetry_service()
    svc.collect_and_export(cpu_count=1)
    ok = svc.export_emissions(duration_seconds=0.5, total_emissions_kg=0.001)

    assert ok is False
    assert len(responses.calls) == 1


@responses.activate
def test_public_uses_telemetry_api_key_not_dashboard_api_key(
    monkeypatch, reset_telemetry_service
):
    monkeypatch.delenv("CODECARBON_API_KEY", raising=False)
    monkeypatch.setenv(TELEMETRY_ENV_VAR, "public")
    monkeypatch.setenv(TELEMETRY_API_KEY_ENV_VAR, "telemetry-only-key")
    monkeypatch.setenv(TELEMETRY_API_ENDPOINT_ENV_VAR, "https://telemetry.test")
    monkeypatch.setattr(telemetry_config_module, "DEFAULT_PUBLIC_TELEMETRY_TOKEN", "")
    monkeypatch.setattr(
        "codecarbon.cli.cli_utils.load_telemetry_config_from_file",
        lambda path=None: {},
    )
    monkeypatch.setattr(
        "codecarbon.core.telemetry.config.load_telemetry_preference",
        lambda: None,
    )
    monkeypatch.setattr(
        telemetry_config_module,
        "get_telemetry_preference_file",
        lambda: Path("/nonexistent/codecarbon-telemetry-pref.txt"),
    )
    monkeypatch.setattr(
        telemetry_config_module,
        "_hierarchical_config_dict",
        lambda: {
            "api_key": "dashboard-key",
            "api_endpoint": "https://dashboard.example",
        },
    )

    responses.add(
        responses.POST,
        "https://telemetry.test/telemetry",
        json={},
        status=201,
    )
    responses.add(
        responses.POST,
        "https://telemetry.test/emissions",
        json={},
        status=200,
    )

    init_telemetry()
    svc = telemetry_service_module.get_telemetry_service()
    svc.collect_and_export(cpu_count=1)
    svc.export_emissions(duration_seconds=2.0, total_emissions_kg=0.001)

    assert responses.calls[1].request.headers.get("x-api-token") == "telemetry-only-key"


@responses.activate
def test_public_dashboard_api_key_alone_does_not_enable_emissions_post(
    monkeypatch, reset_telemetry_service
):
    monkeypatch.delenv(TELEMETRY_API_KEY_ENV_VAR, raising=False)
    monkeypatch.setenv(TELEMETRY_ENV_VAR, "public")
    monkeypatch.setenv(TELEMETRY_API_ENDPOINT_ENV_VAR, "https://telemetry.test")
    monkeypatch.setattr(telemetry_config_module, "DEFAULT_PUBLIC_TELEMETRY_TOKEN", "")
    monkeypatch.setattr(
        "codecarbon.cli.cli_utils.load_telemetry_config_from_file",
        lambda path=None: {},
    )
    monkeypatch.setattr(
        "codecarbon.core.telemetry.config.load_telemetry_preference",
        lambda: None,
    )
    monkeypatch.setattr(
        telemetry_config_module,
        "get_telemetry_preference_file",
        lambda: Path("/nonexistent/codecarbon-telemetry-pref.txt"),
    )
    monkeypatch.setattr(
        telemetry_config_module,
        "_hierarchical_config_dict",
        lambda: {
            "api_key": "dashboard-only",
            "api_endpoint": "https://ignored-for-telemetry-host.test",
        },
    )

    responses.add(
        responses.POST,
        "https://telemetry.test/telemetry",
        json={},
        status=201,
    )

    init_telemetry()
    svc = telemetry_service_module.get_telemetry_service()
    svc.collect_and_export(cpu_count=1)
    ok = svc.export_emissions(duration_seconds=2.0, total_emissions_kg=0.001)

    assert ok is False
    assert len(responses.calls) == 1
