import os
import shutil
import unittest
from unittest import mock

from pandas import read_csv

from codecarbon import EmissionsTracker
from codecarbon.emissions_tracker import TaskEmissionsTracker

OUTPUT_DIR = "test_token_data"


class TestTokenTracking(unittest.TestCase):
    def setUp(self) -> None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def test_record_tokens_accumulates_over_a_task(self):
        tracker = EmissionsTracker(save_to_file=False, allow_multiple_runs=True)
        with TaskEmissionsTracker("inference", tracker=tracker) as task:
            task.record_tokens(input_tokens=10, output_tokens=20)
            task.record_tokens(input_tokens=12, output_tokens=30)
            task.record_tokens(input_tokens=1, output_tokens=2)
        data = tracker._tasks["inference"].out()
        tracker.stop()
        self.assertEqual(23, data.input_tokens)
        self.assertEqual(52, data.output_tokens)
        self.assertEqual(3, data.n_requests)

    def test_record_tokens_without_active_task_warns_and_records_nothing(self):
        tracker = EmissionsTracker(save_to_file=False, allow_multiple_runs=True)
        tracker.start()
        with mock.patch("codecarbon.emissions_tracker.logger") as mock_logger:
            tracker.record_tokens(output_tokens=10)
        tracker.stop()

        self.assertEqual({}, tracker._tasks)
        mock_logger.warning.assert_called_once()
        self.assertIn("No active task", mock_logger.warning.call_args[0][0])

    def test_token_counts_are_written_to_the_task_csv(self):
        tracker = EmissionsTracker(
            output_dir=OUTPUT_DIR,
            experiment_name="tokens",
            allow_multiple_runs=True,
        )
        with TaskEmissionsTracker("inference", tracker=tracker) as task:
            task.record_tokens(input_tokens=4, output_tokens=16)
        tracker.stop()

        task_file = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("emissions_")]
        df = read_csv(os.path.join(OUTPUT_DIR, task_file[0]))
        row = df[df.task_name == "inference"].iloc[0]
        self.assertEqual(4, row.input_tokens)
        self.assertEqual(16, row.output_tokens)
        self.assertEqual(1, row.n_requests)
