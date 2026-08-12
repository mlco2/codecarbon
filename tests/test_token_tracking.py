import os
import shutil
import unittest
from unittest import mock

from pandas import read_csv

from codecarbon import EmissionsTracker
from codecarbon.emissions_tracker import TaskEmissionsTracker
from codecarbon.external.task import extract_token_counts

OUTPUT_DIR = "test_token_data"


class OpenAIUsage:
    prompt_tokens = 12
    completion_tokens = 30


class OpenAIResponse:
    usage = OpenAIUsage()


class VLLMCompletion:
    def __init__(self, n):
        self.token_ids = list(range(n))


class VLLMRequestOutput:
    def __init__(self):
        self.prompt_token_ids = list(range(7))
        self.outputs = [VLLMCompletion(4), VLLMCompletion(6)]


class TestExtractTokenCounts(unittest.TestCase):
    def test_openai_object(self):
        self.assertEqual((12, 30), extract_token_counts(OpenAIResponse()))

    def test_openai_dict(self):
        response = {"usage": {"prompt_tokens": 3, "completion_tokens": 8}}
        self.assertEqual((3, 8), extract_token_counts(response))

    def test_ollama_dict(self):
        response = {"prompt_eval_count": 5, "eval_count": 42, "response": "hi"}
        self.assertEqual((5, 42), extract_token_counts(response))

    def test_vllm_request_output(self):
        self.assertEqual((7, 10), extract_token_counts(VLLMRequestOutput()))

    def test_unknown_response_is_zero(self):
        self.assertEqual((0, 0), extract_token_counts({"text": "hello"}))


class TestTokenTracking(unittest.TestCase):
    def setUp(self) -> None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def test_record_tokens_accumulates_over_a_task(self):
        tracker = EmissionsTracker(save_to_file=False, allow_multiple_runs=True)
        with TaskEmissionsTracker("inference", tracker=tracker) as task:
            task.record_tokens(input_tokens=10, output_tokens=20)
            task.record_tokens(response=OpenAIResponse())
            task.record_tokens(response={"prompt_eval_count": 1, "eval_count": 2})
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

    def test_response_without_usage_logs_a_debug_hint(self):
        tracker = EmissionsTracker(save_to_file=False, allow_multiple_runs=True)
        with TaskEmissionsTracker("inference", tracker=tracker) as task:
            # A streamed OpenAI chunk carries no usage unless the caller asked
            # for stream_options={"include_usage": True}.
            with mock.patch("codecarbon.emissions_tracker.logger") as mock_logger:
                task.record_tokens(response={"choices": [], "usage": None})
        data = tracker._tasks["inference"].out()
        tracker.stop()

        self.assertEqual(
            (0, 0, 1), (data.input_tokens, data.output_tokens, data.n_requests)
        )
        mock_logger.debug.assert_called_once()
        self.assertIn("include_usage", mock_logger.debug.call_args[0][0])

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
