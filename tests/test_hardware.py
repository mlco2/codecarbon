import unittest
from time import sleep
from unittest import mock

from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.external.hardware import CPU, GPU, MODE_CPU_LOAD
from tests.testdata import TWO_GPU_DETAILS_RESPONSE


@mock.patch("codecarbon.core.cpu.is_psutil_available", return_value=True)
@mock.patch("codecarbon.core.cpu.is_powergadget_available", return_value=False)
@mock.patch("codecarbon.core.cpu.is_rapl_available", return_value=False)
class TestCPULoad(unittest.TestCase):
    def test_cpu_total_power(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu.start()
        sleep(0.5)
        self.assertGreater(cpu.total_power().W, 1)

    def test_cpu_load_detection(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        tracker = OfflineEmissionsTracker()
        for hardware in tracker._hardware:
            if isinstance(hardware, CPU) and hardware._mode == MODE_CPU_LOAD:
                break
        else:
            raise Exception("No CPU load !!!")
        tracker.start()
        sleep(0.5)
        emission = tracker.stop()
        self.assertGreater(emission, 0.0)


@mock.patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@mock.patch(
    "codecarbon.external.hardware.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
class TestGPUMetadata(unittest.TestCase):
    def test_gpu_metadata_total_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPU.from_utils()
        self.assertAlmostEqual(0.074318, gpu.total_power().kW, places=2)

    def test_gpu_metadata_one_gpu_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPU.from_utils()
        self.assertAlmostEqual(
            0.032159, gpu._get_power_for_gpus(gpu_ids=[1]).kW, places=2
        )
