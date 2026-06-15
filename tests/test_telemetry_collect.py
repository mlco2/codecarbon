import unittest
from unittest.mock import patch

from codecarbon.core.telemetry import TelemetryContext, TelemetryLevel, build_payload
from codecarbon.core.telemetry.schemas import MINIMAL_TELEMETRY_FIELDS, TelemetryBase, TelemetryCreate
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
    conf = overrides.pop("conf", {"codecarbon_version": "3.0"})
    emissions = overrides.pop("emissions", _sample_emissions())
    output_methods = overrides.pop("output_methods", [])
    return TelemetryContext(
        conf=conf,
        emissions=emissions,
        hardware=overrides.pop("hardware", []),
        resource_tracker=overrides.pop("resource_tracker", None),
        output_methods=output_methods,
        tasks=overrides.pop("tasks", {}),
        measure_power_secs=overrides.pop("measure_power_secs", 15),
        integration=overrides.pop("integration", "library"),
    )


class TestTelemetryCollect(unittest.TestCase):
    def test_build_payload_minimal_omits_run_metrics(self):
        ctx = _tracker_context(
            conf={
                "os": "Linux",
                "codecarbon_version": "3.0",
                "cpu_count": 4,
                "tracking_mode": "machine",
            },
            output_methods=["file"],
        )
        with patch(
            "codecarbon.core.telemetry.collect._package_installed",
            side_effect=lambda name: name == "torch",
        ):
            payload = build_payload(ctx, level=TelemetryLevel.minimal)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertNotIn("total_emissions_kg", payload)
        self.assertNotIn("has_torch", payload)
        self.assertNotIn("output_methods", payload)

    def test_build_payload_extensive_includes_run_and_framework_flags(self):
        ctx = _tracker_context(
            conf={
                "os": "Linux",
                "codecarbon_version": "3.0",
                "cpu_count": 4,
                "tracking_mode": "machine",
            },
            output_methods=["file"],
        )
        with patch(
            "codecarbon.core.telemetry.collect._package_installed",
            side_effect=lambda name: name == "torch",
        ):
            payload = build_payload(ctx, level=TelemetryLevel.extensive)

        self.assertEqual(payload["telemetry_level"], "extensive")
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
            payload = build_payload(ctx, level=TelemetryLevel.extensive)

        self.assertEqual(payload["telemetry_level"], "extensive")
        self.assertTrue(payload["has_torch"])
        self.assertNotIn("torch_version", payload)

    def test_build_payload_uses_resolved_level(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        payload = build_payload(ctx, level=TelemetryLevel.extensive)
        self.assertEqual(payload["telemetry_level"], "extensive")

    def test_minimal_payload_passes_schema_validation(self):
        ctx = _tracker_context(conf={"os": "Linux", "codecarbon_version": "3.0"})
        payload = build_payload(ctx, level=TelemetryLevel.minimal)
        TelemetryCreate(**payload)

    def test_extensive_payload_passes_schema_validation(self):
        ctx = _tracker_context(conf={"os": "Linux", "codecarbon_version": "3.0"})
        payload = build_payload(ctx, level=TelemetryLevel.extensive)
        TelemetryCreate(**payload)

    def test_payload_keys_are_schema_fields(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        for level in (TelemetryLevel.minimal, TelemetryLevel.extensive):
            payload = build_payload(ctx, level=level)
            self.assertTrue(set(payload).issubset(TelemetryBase.model_fields))

    def test_minimal_fields_are_schema_subset(self):
        self.assertTrue(MINIMAL_TELEMETRY_FIELDS.issubset(TelemetryBase.model_fields))


if __name__ == "__main__":
    unittest.main()
