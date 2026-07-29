"""Tests for per-request HTTP tracking on a shared EmissionsTracker."""

import sys
import threading
import time
import unittest
from unittest import mock

from codecarbon.emissions_tracker import EmissionsTracker, HttpRequestBaseline
from codecarbon.external.geography import CloudMetadata
from tests.fake_modules import pynvml as fake_pynvml
from tests.testdata import TWO_GPU_DETAILS_RESPONSE, TWO_GPU_DETAILS_RESPONSE_HANDLES
from tests.testutils import get_custom_mock_open

empty_conf = "[codecarbon]"

if sys.platform == "darwin":
    mock_platform_cli_setup = mock.patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = mock.patch(
        "codecarbon.core.cpu.IntelPowerGadget._setup_cli"
    )


def _build_tracker(**kwargs: object) -> EmissionsTracker:
    defaults: dict[str, object] = {
        "project_name": "http-request-test",
        "save_to_file": False,
        "save_to_api": False,
        "save_to_logger": False,
        "allow_multiple_runs": True,
        "measure_power_secs": 10,
    }
    defaults.update(kwargs)
    return EmissionsTracker(**defaults)


@mock.patch("codecarbon.core.gpu.pynvml", fake_pynvml)
@mock.patch("codecarbon.core.gpu.is_nvidia_system", return_value=True)
@mock.patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@mock.patch(
    "codecarbon.external.hardware.AllGPUDevices.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
@mock.patch(
    "codecarbon.emissions_tracker.EmissionsTracker._get_cloud_metadata",
    return_value=CloudMetadata(provider=None, region=None),
)
@mock.patch("codecarbon.core.cpu.IntelPowerGadget._log_values")
@mock_platform_cli_setup
class TestHttpRequestTracking(unittest.TestCase):
    def setUp(self) -> None:
        fake_pynvml.DETAILS = TWO_GPU_DETAILS_RESPONSE_HANDLES
        patcher = mock.patch(
            "builtins.open", new_callable=get_custom_mock_open(empty_conf, empty_conf)
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_mark_http_request_start_requires_started_tracker(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        with self.assertRaises(RuntimeError):
            tracker.mark_http_request_start("GET /predict")

    def test_http_request_baseline_round_trip(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        baseline = tracker.mark_http_request_start("GET /predict")
        emissions_data = tracker.finish_http_request(baseline)
        tracker.stop()
        self.assertIsNotNone(emissions_data)
        self.assertEqual(baseline.task_name.split("_")[0], "GET /predict")

    def test_http_request_task_names_are_unique_for_same_route(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        first = tracker.mark_http_request_start("GET /predict")
        second = tracker.mark_http_request_start("GET /predict")
        tracker.stop()
        self.assertNotEqual(first.task_name, second.task_name)
        self.assertTrue(second.task_name.startswith("GET /predict"))

    def test_finish_http_request_unknown_task_returns_none(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        baseline = HttpRequestBaseline(
            task_name="missing-task",
            started_at=0.0,
            duration_at_start=0.0,
            emissions=0.0,
            cpu_energy=0.0,
            gpu_energy=0.0,
            ram_energy=0.0,
            energy_consumed=0.0,
            water_consumed=0.0,
        )
        result = tracker.finish_http_request(baseline)
        tracker.stop()
        self.assertIsNone(result)

    def test_persist_completed_task_skips_when_api_disabled(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker(save_to_api=False)
        tracker.start()
        tracker.start_task("GET /predict")
        tracker.stop_task("GET /predict")
        tracker.persist_completed_task("GET /predict")
        tracker.stop()

    @mock.patch("codecarbon.output.CodeCarbonAPIOutput.task_out")
    def test_persist_completed_task_uploads_finished_task(
        self,
        mock_task_out,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker(
            save_to_api=True,
            experiment_id="00000000-0000-0000-0000-000000000001",
            api_key="test-key",
        )
        tracker.start()
        baseline = tracker.mark_http_request_start("GET /predict")
        tracker.finish_http_request(baseline)
        tracker.persist_completed_task(baseline.task_name)
        tracker.stop()
        mock_task_out.assert_called_once()

    def test_mark_http_request_start_empty_task_name_gets_uuid(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        baseline = tracker.mark_http_request_start("")
        tracker.finish_http_request(baseline)
        tracker.stop()
        self.assertTrue(baseline.task_name)
        self.assertNotEqual(baseline.task_name, "")

    @mock.patch("codecarbon.output.CodeCarbonAPIOutput.task_out")
    def test_persist_completed_task_skips_missing_and_incomplete_tasks(
        self,
        mock_task_out,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker(
            save_to_api=True,
            experiment_id="00000000-0000-0000-0000-000000000001",
            api_key="test-key",
        )
        tracker.start()
        tracker.persist_completed_task("does-not-exist")
        baseline = tracker.mark_http_request_start("GET /predict")
        tracker.persist_completed_task(baseline.task_name)
        mock_task_out.assert_not_called()
        tracker.finish_http_request(baseline)
        tracker.persist_completed_task(baseline.task_name)
        tracker.stop()
        mock_task_out.assert_called_once()

    @mock.patch("codecarbon.output.CodeCarbonAPIOutput.task_out")
    def test_persist_completed_task_skips_already_uploaded(
        self,
        mock_task_out,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker(
            save_to_api=True,
            experiment_id="00000000-0000-0000-0000-000000000001",
            api_key="test-key",
        )
        tracker.start()
        baseline = tracker.mark_http_request_start("GET /predict")
        tracker.finish_http_request(baseline)
        tracker.persist_completed_task(baseline.task_name)
        tracker.persist_completed_task(baseline.task_name)
        tracker.stop()
        mock_task_out.assert_called_once()

    def test_finish_http_request_reuses_cached_cloud_metadata(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        first = tracker.mark_http_request_start("GET /predict")
        tracker.finish_http_request(first)
        cloud_calls_after_first_finish = mock_cloud.call_count
        second = tracker.mark_http_request_start("GET /predict")
        tracker.finish_http_request(second)
        tracker.stop()
        self.assertEqual(mock_cloud.call_count, cloud_calls_after_first_finish)

    def test_mark_does_not_block_on_slow_finish(
        self,
        mock_cli_setup,
        mock_log_values,
        mock_cloud,
        mock_gpu_details,
        mock_gpu_available,
        mock_nvidia,
    ) -> None:
        tracker = _build_tracker()
        tracker.start()
        baseline = tracker.mark_http_request_start("GET /predict")
        tracker._last_measured_time = 0.0
        measure_started = threading.Event()
        release_measure = threading.Event()

        original_run = tracker._run_power_measurement

        def slow_measure() -> None:
            measure_started.set()
            release_measure.wait(timeout=5.0)
            original_run()

        with mock.patch.object(
            tracker, "_run_power_measurement", side_effect=slow_measure
        ):
            finish_thread = threading.Thread(
                target=tracker.finish_http_request, args=(baseline,)
            )
            finish_thread.start()
            assert measure_started.wait(timeout=2.0)

            mark_started = time.perf_counter()
            second = tracker.mark_http_request_start("GET /predict")
            elapsed = time.perf_counter() - mark_started

            release_measure.set()
            finish_thread.join(timeout=5.0)

        tracker.stop()
        self.assertLess(elapsed, 0.2)
        self.assertNotEqual(baseline.task_name, second.task_name)
