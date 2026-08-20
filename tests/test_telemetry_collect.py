import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry.collect import (
    OUTPUT_METHOD_LABELS,
    _integration,
    build_payload,
)
from codecarbon.core.telemetry.schemas import (
    MINIMAL_TELEMETRY_FIELDS,
    TelemetryBase,
    TelemetryCreate,
    TelemetryLevel,
)
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


OUTPUT_METHOD_BY_LABEL = {
    label: method for method, label in OUTPUT_METHOD_LABELS.items()
}


def _tracker_context(**overrides):
    """Return a (tracker, emissions) pair standing in for a live tracker."""
    tracker = SimpleNamespace(
        _conf=overrides.pop("conf", {"codecarbon_version": "3.0"}),
        _hardware=overrides.pop("hardware", []),
        _resource_tracker=overrides.pop("resource_tracker", None),
        _output_methods=[
            OUTPUT_METHOD_BY_LABEL[label]
            for label in overrides.pop("output_methods", [])
        ],
        _emissions_endpoint=None,
        _tasks=overrides.pop("tasks", {}),
        _measure_power_secs=overrides.pop("measure_power_secs", 15),
    )
    return tracker, overrides.pop("emissions", _sample_emissions())


def _build(ctx, level=TelemetryLevel.minimal):
    tracker, emissions = ctx
    return build_payload(tracker, emissions, level=level)


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
            payload = _build(ctx, level=TelemetryLevel.minimal)

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
            payload = _build(ctx, level=TelemetryLevel.extensive)

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
            payload = _build(ctx, level=TelemetryLevel.extensive)

        self.assertEqual(payload["telemetry_level"], "extensive")
        self.assertTrue(payload["has_torch"])
        self.assertNotIn("torch_version", payload)

    def test_build_payload_uses_resolved_level(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        payload = _build(ctx, level=TelemetryLevel.extensive)
        self.assertEqual(payload["telemetry_level"], "extensive")

    def test_minimal_payload_passes_schema_validation(self):
        ctx = _tracker_context(conf={"os": "Linux", "codecarbon_version": "3.0"})
        payload = _build(ctx, level=TelemetryLevel.minimal)
        TelemetryCreate(**payload)

    def test_extensive_payload_passes_schema_validation(self):
        ctx = _tracker_context(conf={"os": "Linux", "codecarbon_version": "3.0"})
        payload = _build(ctx, level=TelemetryLevel.extensive)
        TelemetryCreate(**payload)

    def test_payload_keys_are_schema_fields(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        for level in (TelemetryLevel.minimal, TelemetryLevel.extensive):
            payload = _build(ctx, level=level)
            self.assertTrue(set(payload).issubset(TelemetryBase.model_fields))

    def test_minimal_fields_are_schema_subset(self):
        self.assertTrue(MINIMAL_TELEMETRY_FIELDS.issubset(TelemetryBase.model_fields))

    def test_cloud_region_from_aws_metadata(self):
        emissions = _sample_emissions(on_cloud="Y", cloud_region="", region="")
        ctx = _tracker_context(emissions=emissions)
        with patch(
            "codecarbon.core.telemetry.collect.get_env_cloud_details",
            return_value={"provider": "aws", "metadata": {"region": "eu-west-1"}},
        ):
            payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(payload["cloud_provider"], "aws")
        self.assertEqual(payload["cloud_region"], "eu-west-1")

    def test_cloud_region_from_azure_metadata(self):
        emissions = _sample_emissions(on_cloud="Y", cloud_region="", region="")
        ctx = _tracker_context(emissions=emissions)
        with patch(
            "codecarbon.core.telemetry.collect.get_env_cloud_details",
            return_value={
                "provider": "azure",
                "metadata": {"compute": {"location": "westeurope"}},
            },
        ):
            payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(payload["cloud_provider"], "azure")
        self.assertEqual(payload["cloud_region"], "westeurope")

    def test_cloud_region_from_gcp_metadata(self):
        emissions = _sample_emissions(on_cloud="Y", cloud_region="", region="")
        ctx = _tracker_context(emissions=emissions)
        with patch(
            "codecarbon.core.telemetry.collect.get_env_cloud_details",
            return_value={
                "provider": "gcp",
                "metadata": {"zone": "projects/p/zones/europe-west1-b"},
            },
        ):
            payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(payload["cloud_provider"], "gcp")
        self.assertEqual(payload["cloud_region"], "europe-west1")

    def test_extensive_payload_includes_environment_hints(self):
        ctx = _tracker_context(output_methods=["api"])
        with patch.dict(
            os.environ,
            {
                "CONDA_DEFAULT_ENV": "base",
                "KUBERNETES_SERVICE_HOST": "10.0.0.1",
                "CURSOR_TRACE_ID": "trace-1",
                "COLAB_GPU": "0",
            },
            clear=False,
        ):
            payload = _build(ctx, level=TelemetryLevel.extensive)
        self.assertEqual(payload["python_env_type"], "conda")
        self.assertEqual(payload["api_mode"], "online")
        self.assertTrue(payload["in_container"])
        self.assertEqual(payload["container_runtime"], "kubernetes")
        self.assertEqual(payload["ide_used"], "cursor")
        self.assertEqual(payload["notebook_environment"], "colab")

    def test_integration_detects_cli_monitor(self):
        tracker, _ = _tracker_context()
        with patch.object(sys, "argv", ["codecarbon", "monitor", "train.py"]):
            self.assertEqual(_integration(tracker), "cli_monitor")

    def test_hardware_diagnostics_lists_tracked_hardware(self):
        hardware = MagicMock()
        hardware.description.return_value = "CPU: test"
        ctx = _tracker_context(
            hardware=[hardware],
            resource_tracker=MagicMock(gpu_tracker="pynvml"),
        )
        with patch(
            "codecarbon.core.telemetry.collect.platform.system", return_value="Linux"
        ):
            with patch(
                "codecarbon.core.cpu.is_rapl_available",
                return_value=True,
            ):
                payload = _build(ctx, level=TelemetryLevel.extensive)
        self.assertIn("CPU: test", payload["hardware_tracked"])
        self.assertTrue(payload["hardware_detection_success"])
        self.assertTrue(payload["rapl_available"])
        self.assertEqual(payload["gpu_detection_method"], "pynvml")

    def test_gpu_static_fields_when_nvidia_available(self):
        ctx = _tracker_context()
        mock_mem = MagicMock(total=8 * 1024**3)
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem
        mock_pynvml.nvmlSystemGetCudaDriverVersion_v2.return_value = 12040
        mock_pynvml.nvmlSystemGetDriverVersion.return_value = "535.0"
        with patch(
            "codecarbon.core.telemetry.collect.is_nvidia_system",
            return_value=True,
        ):
            with patch.dict(sys.modules, {"pynvml": mock_pynvml}):
                payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(payload["gpu_memory_total_gb"], 8.0)
        self.assertEqual(payload["cuda_version"], "12.4")
        self.assertEqual(payload["gpu_driver_version"], "535.0")

    def test_extensive_payload_detects_docker_and_jupyter(self):
        ctx = _tracker_context()
        with patch("os.path.exists", return_value=True):
            with patch(
                "codecarbon.core.telemetry.collect._detect_notebook_environment",
                return_value="jupyter",
            ):
                payload = _build(ctx, level=TelemetryLevel.extensive)
        self.assertTrue(payload["in_container"])
        self.assertEqual(payload["container_runtime"], "docker")
        self.assertEqual(payload["notebook_environment"], "jupyter")

    def test_minimal_payload_detects_virtualenv(self):
        ctx = _tracker_context()
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/venv"}, clear=False):
            with patch(
                "codecarbon.core.telemetry.collect.sys.prefix",
                "/venv",
                create=True,
            ):
                with patch(
                    "codecarbon.core.telemetry.collect.sys.base_prefix",
                    "/usr",
                    create=True,
                ):
                    payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(payload["python_env_type"], "venv")


if __name__ == "__main__":
    unittest.main()
