import time
import unittest
from typing import List

from codecarbon.emissions_tracker import (
    EmissionsTracker,
    track_emissions,
)
from codecarbon.output import (
    BaseOutput, EmissionsData,
)


def heavy_computation(run_time_secs: int = 3):
    end_time: float = time.time() + run_time_secs  # Run for `run_time_secs` seconds
    while time.time() < end_time:
        pass


class CustomOutput(BaseOutput):
    def __init__(self):
        self.log: List[EmissionsData] = list()

    def out(self, data: EmissionsData):
        self.log.append(data)


class TestCarbonCustomHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestCarbonCustomHandler"
        self.emissions_logfile = "emissions-test-TestCarbonCustomHandler.log"

    def test_carbon_tracker_custom_handler(self):
        handler_0 = CustomOutput()
        handler_1 = CustomOutput()
        tracker = EmissionsTracker(
            project_name=self.project_name,
            output_handlers=[handler_0, handler_1],
            api_call_interval=1,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()

        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_logging_output(handler_0)
        self.verify_logging_output(handler_1)

    def test_decorator_flush(self):
        handler_0 = CustomOutput()
        handler_1 = CustomOutput()

        @track_emissions(
            project_name=self.project_name,
            save_to_logger=True,
            output_handlers=[handler_0, handler_1],
            api_call_interval=1,
        )
        def dummy_train_model():
            heavy_computation(run_time_secs=1)
            # I don't know how to call flush() in decorator mode
            return 42

        dummy_train_model()
        self.verify_logging_output(handler_0)
        self.verify_logging_output(handler_1)

    def verify_logging_output(self, handler: CustomOutput, expected_lines=1) -> None:
        assert len(handler.log) == expected_lines
        results = handler.log[0]
        self.assertEqual(results.project_name, self.project_name)
        self.assertNotEqual(results.emissions, 0.0)
        self.assertAlmostEqual(results.emissions, 6.262572537957655e-05, places=2)
