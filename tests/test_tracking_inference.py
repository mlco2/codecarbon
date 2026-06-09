import os
import shutil
import time
import unittest

from pandas import read_csv

from codecarbon import EmissionsTracker

OUTPUT_DIR = "test_task_data"


def heavy_computation(run_time_secs: float = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        _ = 1e9 / 1e10


def mock_load_model():
    model = [str(i) for i in range(100_000)]

    return model


class InferenceClass:
    def __init__(self):
        self.model = mock_load_model()

    def predict(self, input_data):
        heavy_computation(input_data)


class TestCarbonInferenceTracker(unittest.TestCase):
    def setUp(self) -> None:
        tmp_dir = OUTPUT_DIR
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

    def tearDown(self) -> None:
        tmp_dir = OUTPUT_DIR
        shutil.rmtree(tmp_dir)

    def test_tracker_measures_model_loading_task(self):
        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        tracker.start()
        tracker.start_task("model_loading")
        inference_class = InferenceClass()
        tracker.stop_task("model_loading")
        del inference_class
        model_loading_task = tracker._tasks["model_loading"]
        actual_cpu_energy = model_loading_task.emissions_data.cpu_energy
        actual_gpu_energy = model_loading_task.emissions_data.gpu_energy
        actual_ram_energy = model_loading_task.emissions_data.ram_energy
        tracker.stop()

        # Then
        assert actual_cpu_energy < tracker.final_emissions_data.cpu_energy
        assert actual_gpu_energy <= tracker.final_emissions_data.gpu_energy
        assert actual_ram_energy < tracker.final_emissions_data.ram_energy

    def test_tracker_measures_correctly_each_inference_from_task(self):
        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        tracker.start()

        tracker.start_task("model_loading")
        inference_class = InferenceClass()
        tracker.stop_task("model_loading")
        nb_inferences = 3
        for i in range(nb_inferences):
            inference_task_name = "inference_" + str(i)
            tracker.start_task(inference_task_name)
            inference_class.predict(i)
            tracker.stop_task(inference_task_name)
        del inference_class
        tasks = tracker._tasks
        tracker.stop()

        assert len(tasks) == nb_inferences + 1

    def test_tracker_outputs_data_point_for_each_task_logged(self):
        experiment_name = "base_2"
        tracker = EmissionsTracker(
            measure_power_secs=1,
            save_to_file=True,
            output_dir=OUTPUT_DIR,
            experiment_name=experiment_name,
        )
        expected_task_list = [
            "model_loading",
            "inference_0",
            "inference_1",
            "inference_2",
        ]

        tracker.start()

        tracker.start_task("model_loading")
        run_id = tracker.run_id.__str__()
        inference_class = InferenceClass()
        tracker.stop_task("model_loading")

        for i in range(3):
            inference_task_name = "inference_" + str(i)
            tracker.start_task(inference_task_name)
            inference_class.predict(i)
            tracker.stop_task(inference_task_name)

        tracker.stop()

        task_file_path = "emissions_" + experiment_name + "_" + run_id + ".csv"
        actual_task_data = read_csv(os.path.join(OUTPUT_DIR, task_file_path))

        assert expected_task_list == list(actual_task_data.task_name)
