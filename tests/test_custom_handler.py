import time
import unittest
from typing import List

from codecarbon.emissions_tracker import EmissionsTracker, track_emissions
from codecarbon.output import BaseOutput, EmissionsData


def heavy_computation(run_time_secs: int = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


class CustomOutput(BaseOutput):
    def __init__(self):
        self.log: List[EmissionsData] = list()

    def live_out(self, delta: EmissionsData, total: EmissionsData):
        self.log.append(total)


class TestCarbonCustomHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestCarbonCustomHandler"

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
        self.verify_custom_handler_state(handler_0)
        self.verify_custom_handler_state(handler_1)

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
            return 42

        dummy_train_model()
        self.verify_custom_handler_state(handler_0)
        self.verify_custom_handler_state(handler_1)

    def verify_custom_handler_state(
        self, handler: CustomOutput, expected_lines=1
    ) -> None:
        assert len(handler.log) == expected_lines
        results = handler.log[0]
        self.assertEqual(results.project_name, self.project_name)
        self.assertNotEqual(results.emissions, 0.0)
        self.assertAlmostEqual(results.emissions, 6.262572537957655e-05, places=2)
