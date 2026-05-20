import unittest
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry import TelemetryContext, TelemetryLevel, build_payload
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


def _tracker_context(**overrides) -> TelemetryContext:
    tracker = MagicMock()
    tracker._conf = overrides.pop("conf", {"codecarbon_version": "3.0"})
    tracker._hardware = overrides.pop("hardware", [])
    tracker._resource_tracker = overrides.pop("resource_tracker", None)
    tracker._save_to_file = overrides.pop("save_to_file", False)
    tracker._save_to_api = overrides.pop("save_to_api", False)
    tracker._save_to_logger = overrides.pop("save_to_logger", False)
    tracker._emissions_endpoint = overrides.pop("emissions_endpoint", None)
    tracker._save_to_prometheus = overrides.pop("save_to_prometheus", False)
    tracker._save_to_logfire = overrides.pop("save_to_logfire", False)
    tracker._tasks = overrides.pop("tasks", {})
    tracker._measure_power_secs = overrides.pop("measure_power_secs", 15)
    tracker._is_offline = overrides.pop("is_offline", False)
    emissions = overrides.pop("emissions", _sample_emissions())
    ctx = TelemetryContext(
        conf=tracker._conf,
        emissions=emissions,
        hardware=tracker._hardware,
        resource_tracker=tracker._resource_tracker,
        save_to_api=tracker._save_to_api,
        save_to_file=tracker._save_to_file,
        save_to_logger=tracker._save_to_logger,
        save_to_prometheus=tracker._save_to_prometheus,
        save_to_logfire=tracker._save_to_logfire,
        emissions_endpoint=tracker._emissions_endpoint,
        tasks=tracker._tasks,
        measure_power_secs=tracker._measure_power_secs,
        is_offline=tracker._is_offline,
    )
    return ctx


class TestTelemetryCollect(unittest.TestCase):
    def test_build_payload_includes_run_and_framework_flags(self):
        ctx = _tracker_context(
            conf={
                "os": "Linux",
                "codecarbon_version": "3.0",
                "cpu_count": 4,
                "tracking_mode": "machine",
            },
            save_to_file=True,
        )
        with patch(
            "codecarbon.core.telemetry.collect._package_installed",
            side_effect=lambda name: name == "torch",
        ):
            payload = build_payload(ctx)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertEqual(payload["total_emissions_kg"], 0.5)
        self.assertEqual(payload["duration_seconds"], 10.0)
        self.assertTrue(payload["has_torch"])
        self.assertIn("file", payload["output_methods"])

    def test_build_payload_omits_framework_versions(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0", "hardware": ["cpu"]})
        with patch(
            "codecarbon.core.telemetry.collect._package_installed",
            return_value=True,
        ):
            payload = build_payload(ctx)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertTrue(payload["has_torch"])
        self.assertNotIn("torch_version", payload)

    def test_build_payload_uses_resolved_level(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        payload = build_payload(ctx, level=TelemetryLevel.extensive)
        self.assertEqual(payload["telemetry_level"], "extensive")


if __name__ == "__main__":
    unittest.main()
