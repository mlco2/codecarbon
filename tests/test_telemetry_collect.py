import unittest
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry_collect import (
    build_telemetry_payload,
    collect_telemetry_context,
    project_private_telemetry,
)
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.output_methods.emissions_data import EmissionsData


def _sample_emissions(**overrides):
    base = dict(
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
        os="Linux",
        python_version="3.11",
        codecarbon_version="3.0",
        cpu_count=4,
        cpu_model="cpu",
        gpu_count=1,
        gpu_model="gpu",
        longitude=0.0,
        latitude=0.0,
        ram_total_size=16.0,
        tracking_mode="machine",
    )
    base.update(overrides)
    return EmissionsData(**base)


class TestTelemetryCollect(unittest.TestCase):
    def test_project_private_telemetry_includes_run_and_framework_flags(self):
        tracker = MagicMock()
        tracker._conf = {
            "os": "Linux",
            "codecarbon_version": "3.0",
            "cpu_count": 4,
            "tracking_mode": "machine",
        }
        tracker._geo = None
        tracker._save_to_file = True
        tracker._save_to_api = False
        tracker._save_to_logger = False
        tracker._emissions_endpoint = None
        tracker._save_to_prometheus = False
        tracker._save_to_logfire = False
        tracker._tasks = {}
        tracker._measure_power_secs = 15
        tracker._hardware = []
        tracker._resource_tracker = None

        emissions = _sample_emissions()
        with patch(
            "codecarbon.core.telemetry_collect._package_installed",
            side_effect=lambda name: name == "torch",
        ):
            context = collect_telemetry_context(tracker, emissions)
        payload = project_private_telemetry(context)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertEqual(payload["total_emissions_kg"], 0.5)
        self.assertEqual(payload["duration_seconds"], 10.0)
        self.assertTrue(payload["has_torch"])
        self.assertIn("file", payload["output_methods"])

    def test_build_telemetry_payload_omits_framework_versions(self):
        tracker = MagicMock()
        tracker._conf = {"codecarbon_version": "3.0", "hardware": ["cpu"]}
        tracker._geo = None
        tracker._save_to_file = False
        tracker._save_to_api = False
        tracker._save_to_logger = False
        tracker._emissions_endpoint = None
        tracker._save_to_prometheus = False
        tracker._save_to_logfire = False
        tracker._tasks = {}
        tracker._measure_power_secs = 15
        tracker._hardware = []
        tracker._resource_tracker = None

        emissions = _sample_emissions()
        with patch(
            "codecarbon.core.telemetry_collect._package_installed",
            return_value=True,
        ):
            payload = build_telemetry_payload(tracker, emissions)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertTrue(payload["has_torch"])
        self.assertNotIn("torch_version", payload)

    def test_build_telemetry_payload_uses_resolved_level(self):
        tracker = MagicMock()
        tracker._conf = {"codecarbon_version": "3.0"}
        tracker._save_to_file = False
        tracker._save_to_api = False
        tracker._save_to_logger = False
        tracker._emissions_endpoint = None
        tracker._save_to_prometheus = False
        tracker._save_to_logfire = False
        tracker._tasks = {}
        tracker._measure_power_secs = 15
        tracker._hardware = []
        tracker._resource_tracker = None

        emissions = _sample_emissions()
        payload = build_telemetry_payload(
            tracker, emissions, level=TelemetryLevel.extensive
        )
        self.assertEqual(payload["telemetry_level"], "extensive")
