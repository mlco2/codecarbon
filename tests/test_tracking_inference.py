import time
import unittest

from codecarbon import EmissionsTracker


def heavy_computation(run_time_secs: float = 3):
    end_time: float = time.time() + run_time_secs  # Run for `run_time_secs` seconds
    while time.time() < end_time:
        pass


def mock_load_model():
    model = [str(i) for i in range(100000000)]

    return model


class InferenceClass:
    def __init__(self):
        self.model = mock_load_model()

    def predict(self, input_data):
        heavy_computation(input_data)


class TestCarbonInferenceTracker(unittest.TestCase):
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

        for i in range(10):
            inference_task_name = "inference_" + str(i)
            tracker.start_task(inference_task_name)
            inference_class.predict(i)
            tracker.stop_task(inference_task_name)
        del inference_class
        tasks = tracker._tasks
        tracker.stop()

        assert len(tasks) == 11
