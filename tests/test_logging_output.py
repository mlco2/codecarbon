import json
import logging
import os
import tempfile
import time
import unittest

from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from codecarbon.output import LoggerOutput


def heavy_computation(run_time_secs: int = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


class TestCarbonTrackerFlush(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestCarbonLoggingOutput"
        self.emissions_logfile = "emissions-test-TestCarbonLoggingOutput.log"
        self.emissions_path = tempfile.gettempdir()
        self.emissions_file_path = os.path.join(
            self.emissions_path, self.emissions_logfile
        )
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)
        self._test_logger = logging.getLogger(self.project_name)
        _channel = logging.FileHandler(self.emissions_file_path)
        self._test_logger.addHandler(_channel)
        self._test_logger.setLevel(logging.INFO)
        self.external_logger = LoggerOutput(self._test_logger, logging.INFO)

    def tearDown(self) -> None:
        for handler in self._test_logger.handlers[:]:
            self._test_logger.removeHandler(handler)
            handler.close()
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def test_carbon_tracker_online_logging_output(self):
        tracker = EmissionsTracker(
            project_name=self.project_name,
            save_to_logger=True,
            logging_logger=self.external_logger,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        # tracker.flush()
        # heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_logging_output(self.emissions_file_path)

    def test_carbon_tracker_offline_logging_output(self):
        tracker = OfflineEmissionsTracker(
            project_name=self.project_name,
            country_iso_code="USA",
            save_to_logger=True,
            logging_logger=self.external_logger,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        # tracker.flush()
        # heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_logging_output(self.emissions_file_path)

    def test_decorator_flush(self):
        @track_emissions(
            project_name=self.project_name,
            save_to_logger=True,
            logging_logger=self.external_logger,
        )
        def dummy_train_model():
            heavy_computation(run_time_secs=1)
            # I don't know how to call flush() in decorator mode
            return 42

        res = dummy_train_model()
        self.assertEqual(res, 42)

        self.verify_logging_output(self.emissions_file_path, 1)

    def verify_logging_output(self, file_path: str, expected_lines=1) -> None:
        with open(file_path, "r") as f:
            lines = [line.rstrip() for line in f]
        assert len(lines) == expected_lines
        results = json.loads(lines[0])
        self.assertEqual(results["project_name"], self.project_name)
        self.assertNotEqual(results["emissions"], 0.0)
        self.assertAlmostEqual(results["emissions"], 6.262572537957655e-05, places=2)
