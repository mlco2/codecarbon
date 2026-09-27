import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry.collect import build_payload
from codecarbon.core.telemetry.schemas import (
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


def _tracker_context(**overrides):
    """Return a (tracker, emissions) pair standing in for a live tracker."""
    tracker = SimpleNamespace(
        _conf=overrides.pop("conf", {"codecarbon_version": "3.0"})
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
        )
        payload = _build(ctx, level=TelemetryLevel.minimal)

        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertNotIn("total_emissions_kg", payload)

    def test_timestamp_is_truncated_to_the_hour(self):
        from datetime import datetime, timezone

        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        with patch("codecarbon.core.telemetry.collect.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2026, 1, 1, 12, 34, 56, 789, tzinfo=timezone.utc
            )
            payload = _build(ctx, level=TelemetryLevel.minimal)
        self.assertEqual(
            payload["timestamp"],
            datetime(2026, 1, 1, 12, 0, 0, 0, tzinfo=timezone.utc),
        )

    def test_minimal_payload_passes_schema_validation(self):
        ctx = _tracker_context(conf={"os": "Linux", "codecarbon_version": "3.0"})
        payload = _build(ctx, level=TelemetryLevel.minimal)
        TelemetryCreate(**payload)

    def test_payload_keys_are_schema_fields(self):
        ctx = _tracker_context(conf={"codecarbon_version": "3.0"})
        payload = _build(ctx)
        self.assertTrue(set(payload).issubset(TelemetryBase.model_fields))

    def test_cloud_fields_come_from_tracker_detection(self):
        """No second metadata probe: stop() must not pay for it off-cloud."""
        emissions = _sample_emissions(
            on_cloud="Y", cloud_provider="aws", cloud_region="eu-west-1", region=""
        )
        payload = _build(
            _tracker_context(emissions=emissions), level=TelemetryLevel.minimal
        )
        self.assertEqual(payload["cloud_provider"], "aws")
        self.assertEqual(payload["cloud_region"], "eu-west-1")
        self.assertEqual(payload["region"], "eu-west-1")

    def test_default_geo_fallback_is_not_reported_as_a_location(self):
        """When both geo APIs fail the tracker assumes Canada; telemetry must
        not record that guess as where the user is."""
        tracker, emissions = _tracker_context(
            emissions=_sample_emissions(
                country_name="Canada", country_iso_code="CAN", region="quebec"
            )
        )
        tracker._geo = SimpleNamespace(is_default=True)
        payload = build_payload(tracker, emissions, level=TelemetryLevel.minimal)
        self.assertNotIn("country_name", payload)
        self.assertNotIn("country_iso_code", payload)
        self.assertNotIn("region", payload)

    def test_coordinates_are_never_sent(self):
        emissions = _sample_emissions(longitude=-7.61743, latitude=33.58229)
        payload = _build(
            _tracker_context(
                conf={"longitude": 2.35, "latitude": 48.85}, emissions=emissions
            )
        )
        self.assertNotIn("longitude", payload)
        self.assertNotIn("latitude", payload)

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

    def test_python_env_type_variants(self):
        from codecarbon.core.telemetry import collect

        cases = [
            ({"CONDA_DEFAULT_ENV": "base"}, "/usr", "conda"),
            ({}, "/venv", "venv"),
            ({}, "/usr", "system"),
        ]
        for env, prefix, expected in cases:
            with self.subTest(expected=expected):
                with (
                    patch.dict(os.environ, env, clear=True),
                    patch.object(collect.sys, "prefix", prefix),
                    patch.object(collect.sys, "base_prefix", "/usr"),
                ):
                    self.assertEqual(collect._detect_python_env_type(), expected)

    def test_codecarbon_install_method(self):
        from codecarbon.core.telemetry import collect

        def dist(editable=False, installer=None):
            return SimpleNamespace(
                editable=editable,
                metadata={"Installer": installer} if installer else {},
            )

        cases = [
            (dist(editable=True), "editable"),
            (dist(installer="uv"), "uv"),
            (dist(installer="pip"), "pip"),
            (dist(installer="poetry"), None),
            (RuntimeError("no metadata"), None),
        ]
        for result, expected in cases:
            with self.subTest(expected=expected, result=result):
                with patch(
                    "importlib.metadata.distribution",
                    side_effect=[result],
                ):
                    self.assertEqual(
                        collect._detect_codecarbon_install_method(), expected
                    )

    def test_cudnn_version(self):
        from codecarbon.core.telemetry import collect

        torch_ok = SimpleNamespace(
            backends=SimpleNamespace(cudnn=SimpleNamespace(version=lambda: 8902))
        )
        torch_none = SimpleNamespace(
            backends=SimpleNamespace(cudnn=SimpleNamespace(version=lambda: None))
        )
        torch_broken = SimpleNamespace(backends=None)
        cases = [(torch_ok, "8902"), (torch_none, None), (torch_broken, None)]
        for torch, expected in cases:
            with self.subTest(expected=expected):
                with (
                    patch.object(collect, "_package_installed", return_value=True),
                    patch.dict(sys.modules, {"torch": torch}),
                ):
                    self.assertEqual(collect._cudnn_version(), expected)

    def test_gpu_static_fields_empty_when_nvml_fails(self):
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit.side_effect = RuntimeError("no driver")
        with (
            patch(
                "codecarbon.core.telemetry.collect.is_nvidia_system",
                return_value=True,
            ),
            patch.dict(sys.modules, {"pynvml": mock_pynvml}),
        ):
            payload = _build(_tracker_context())
        self.assertNotIn("gpu_driver_version", payload)


if __name__ == "__main__":
    unittest.main()
