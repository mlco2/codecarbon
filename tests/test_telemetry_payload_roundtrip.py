"""Verify SDK telemetry payloads match the server schema and shared defaults."""

import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from codecarbon.core.telemetry.collect import TelemetryContext, build_payload
from codecarbon.core.telemetry.defaults import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
)
from codecarbon.core.telemetry.schemas import TelemetryCreate as CoreTelemetryCreate
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings
from codecarbon.core.telemetry.client import post_private
from codecarbon.output_methods.emissions_data import EmissionsData

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_TELEMETRY_SCHEMA_PATH = (
    REPO_ROOT / "carbonserver" / "carbonserver" / "api" / "schemas_telemetry.py"
)


def _load_server_telemetry_create():
    spec = importlib.util.spec_from_file_location(
        "server_telemetry_schemas",
        SERVER_TELEMETRY_SCHEMA_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TelemetryCreate


def _sample_emissions() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-01-01T00:00:00",
        project_name="p",
        run_id="r",
        experiment_id="e",
        duration=10.0,
        emissions=0.5,
        emissions_rate=0.05,
        cpu_power=1.0,
        gpu_power=2.0,
        ram_power=0.5,
        cpu_energy=0.01,
        gpu_energy=0.02,
        ram_energy=0.001,
        energy_consumed=0.031,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="idf",
        cloud_provider="",
        cloud_region="",
        os="Linux-5.10.0-x86_64",
        python_version="3.11.5",
        codecarbon_version="3.2.6",
        cpu_count=12,
        cpu_model="Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
        gpu_count=0,
        gpu_model="",
        longitude=2.3,
        latitude=48.8,
        ram_total_size=16.0,
        tracking_mode="machine",
    )


def _tracker_context(**overrides) -> TelemetryContext:
    conf = overrides.pop(
        "conf",
        {
            "os": "Linux-5.10.0-x86_64",
            "codecarbon_version": "3.2.6",
            "cpu_count": 12,
            "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
            "python_version": "3.11.5",
            "tracking_mode": "machine",
        },
    )
    return TelemetryContext(
        conf=conf,
        emissions=overrides.pop("emissions", _sample_emissions()),
        hardware=overrides.pop("hardware", []),
        resource_tracker=overrides.pop("resource_tracker", None),
        output_methods=overrides.pop("output_methods", []),
        tasks=overrides.pop("tasks", {}),
        measure_power_secs=overrides.pop("measure_power_secs", 15),
        integration=overrides.pop("integration", "library"),
    )


def _sdk_request_body(level: TelemetryLevel = TelemetryLevel.minimal) -> dict:
    payload = build_payload(_tracker_context(), level=level)
    return CoreTelemetryCreate(**payload).model_dump(mode="json", exclude_none=True)


class TestTelemetryPayloadContract(unittest.TestCase):
    def test_shared_defaults_are_symlinked(self):
        client_defaults_path = REPO_ROOT / "codecarbon" / "core" / "telemetry" / "defaults.py"
        server_defaults_path = (
            REPO_ROOT / "carbonserver" / "carbonserver" / "telemetry_defaults.py"
        )
        shared_defaults_path = REPO_ROOT / "shared" / "telemetry_defaults.py"

        self.assertTrue(client_defaults_path.is_symlink())
        self.assertTrue(server_defaults_path.is_symlink())
        self.assertEqual(client_defaults_path.resolve(), shared_defaults_path.resolve())
        self.assertEqual(server_defaults_path.resolve(), shared_defaults_path.resolve())

    def test_default_settings_use_shared_token_and_experiment(self):
        settings = TelemetrySettings.resolve()
        self.assertEqual(settings.api_key, DEFAULT_TELEMETRY_API_KEY)
        self.assertEqual(settings.experiment_id, DEFAULT_TELEMETRY_EXPERIMENT_ID)

    def test_minimal_sdk_payload_is_accepted_by_server_schema(self):
        ServerTelemetryCreate = _load_server_telemetry_create()
        request_body = _sdk_request_body()

        parsed = ServerTelemetryCreate.model_validate(request_body)

        self.assertEqual(parsed.telemetry_level, "minimal")
        self.assertEqual(parsed.os, request_body["os"])
        self.assertEqual(parsed.country_name, request_body["country_name"])
        self.assertIsNone(parsed.total_emissions_kg)

    def test_extensive_sdk_payload_is_accepted_by_server_schema(self):
        ServerTelemetryCreate = _load_server_telemetry_create()
        request_body = _sdk_request_body(level=TelemetryLevel.extensive)

        parsed = ServerTelemetryCreate.model_validate(request_body)

        self.assertEqual(parsed.telemetry_level, "extensive")
        self.assertEqual(parsed.total_emissions_kg, request_body["total_emissions_kg"])
        self.assertEqual(parsed.duration_seconds, request_body["duration_seconds"])
        self.assertEqual(
            parsed.decorator_vs_context, request_body["decorator_vs_context"]
        )

    def test_post_private_sends_shared_token_and_round_tripped_body(self):
        ServerTelemetryCreate = _load_server_telemetry_create()
        request_body = _sdk_request_body()
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_api_url": "http://test.example"}
        )

        with patch("codecarbon.core.telemetry.client.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            self.assertTrue(post_private(settings, deepcopy(request_body)))

        self.assertEqual(
            mock_post.call_args.kwargs["headers"]["x-api-token"],
            DEFAULT_TELEMETRY_API_KEY,
        )
        sent_body = mock_post.call_args.kwargs["json"]
        ServerTelemetryCreate.model_validate(sent_body)
        self.assertEqual(sent_body["telemetry_level"], "minimal")
        self.assertEqual(sent_body["os"], request_body["os"])


if __name__ == "__main__":
    unittest.main()
