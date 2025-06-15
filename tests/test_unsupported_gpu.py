import os
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from codecarbon import EmissionsTracker


class TestUnsupportedGPU(unittest.TestCase):

    def setUp(self):
        self.output_csv = "emissions_unsupported_gpu.csv"
        self.NVMLError_NotSupported = type("NVMLError_NotSupported", (Exception,), {})
        self.NVML_ERROR_NOT_SUPPORTED = 10

    def tearDown(self):
        if os.path.exists(self.output_csv):
            os.remove(self.output_csv)

    @patch("codecarbon.core.gpu.pynvml")
    def test_emissions_tracker_unsupported_gpu(self, mock_pynvml):
        mock_pynvml.NVMLError_NotSupported = self.NVMLError_NotSupported
        mock_pynvml.NVMLError = (
            Exception  # Set up the base exception class that gpu.py expects
        )
        mock_pynvml.NVML_ERROR_NOT_SUPPORTED = self.NVML_ERROR_NOT_SUPPORTED

        mock_pynvml.nvmlInit.return_value = None
        mock_pynvml.nvmlShutdown.return_value = None
        mock_pynvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = "dummy_handle"
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle

        mock_pynvml.nvmlDeviceGetName.return_value = b"Test GPU"
        mock_pynvml.nvmlDeviceGetUUID.return_value = b"GPU-UUID-TEST"

        mock_memory_info = MagicMock()
        mock_memory_info.total = 1024 * 1024 * 1024
        mock_memory_info.used = 0
        mock_memory_info.free = mock_memory_info.total
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory_info

        mock_pynvml.nvmlDeviceGetEnforcedPowerLimit.return_value = 250000

        not_supported_error = self.NVMLError_NotSupported(self.NVML_ERROR_NOT_SUPPORTED)
        mock_pynvml.nvmlDeviceGetTotalEnergyConsumption.side_effect = (
            not_supported_error
        )
        mock_pynvml.nvmlDeviceGetPowerUsage.side_effect = not_supported_error

        mock_pynvml.nvmlDeviceGetTemperature.return_value = 50
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = MagicMock(
            gpu=0, memory=0
        )
        mock_pynvml.nvmlDeviceGetDisplayMode.return_value = 0
        mock_pynvml.nvmlDeviceGetPersistenceMode.return_value = 0
        mock_pynvml.nvmlDeviceGetComputeMode.return_value = 0
        mock_pynvml.nvmlDeviceGetComputeRunningProcesses.return_value = []
        mock_pynvml.nvmlDeviceGetGraphicsRunningProcesses.return_value = []

        def simple_work_function():
            # Do some work
            _ = sum(range(10000))

        try:
            # Using EmissionsTracker as a context manager
            with EmissionsTracker(
                output_file=self.output_csv, log_level="error", save_to_file=True
            ):
                simple_work_function()
            # The file should be written upon exiting the 'with' block.

        except AssertionError as e:
            self.fail(f"AssertionError should not be raised by EmissionsTracker: {e}")
        except Exception as e:
            self.fail(
                f"An unexpected exception occurred during EmissionsTracker operation: {e}"
            )

        self.assertTrue(
            os.path.exists(self.output_csv),
            f"Output CSV {self.output_csv} was not created.",
        )

        try:
            df = pd.read_csv(self.output_csv)
        except pd.errors.EmptyDataError:
            self.fail(f"Output CSV {self.output_csv} is empty.")
        except Exception as e:
            self.fail(f"Failed to read or parse CSV {self.output_csv}: {e}")

        self.assertIn("timestamp", df.columns)
        self.assertIn("project_name", df.columns)
        self.assertIn("duration", df.columns)
        self.assertIn("cpu_energy", df.columns)
        self.assertIn("gpu_energy", df.columns)
        self.assertIn("ram_energy", df.columns)
        self.assertIn("cpu_power", df.columns)
        self.assertIn("gpu_power", df.columns)
        self.assertIn("ram_power", df.columns)

        self.assertGreater(df["duration"].iloc[0], 0)
        # CPU energy can be very low for such a short task, sometimes even 0 if precision is an issue
        # or if the measurement interval doesn't capture it.
        # For robustness, let's ensure it's not negative, and if it's positive, that's good.
        # Given the short duration, we'll assert it's >= 0.
        self.assertGreaterEqual(df["cpu_energy"].iloc[0], 0)
        self.assertGreater(
            df["ram_energy"].iloc[0], 0
        )  # RAM energy is usually consistently positive

        self.assertEqual(df["gpu_energy"].iloc[0], 0.0)
        self.assertEqual(df["gpu_power"].iloc[0], 0.0)


if __name__ == "__main__":
    try:
        import pandas
    except ImportError:
        print(
            "Pandas not found. Please install pandas to run this test: pip install pandas"
        )
        exit(1)

    unittest.main()
