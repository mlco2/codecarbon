import os
import unittest
from unittest import mock

import pytest

from codecarbon.core.cpu import IntelPowerGadget
from codecarbon.external.hardware import GPU
from tests.testdata import TWO_GPU_DETAILS_RESPONSE


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


class TestIntelPowerGadget(unittest.TestCase):
    @pytest.mark.integ_test
    def test_intel_power_gadget(self):
        power_gadget = IntelPowerGadget()
        cpu_details = power_gadget.get_cpu_details()
        assert len(cpu_details) > 0

    def test_get_cpu_details(self):
        expected_cpu_details = {
            "Unnamed: 0": 5.5,
            "CPU Utilization(%)": 10.019916666666667,
            "CPU Frequency_0(MHz)": 1792.0,
            "CPU Min Frequency_0(MHz)": 1200.0,
            "CPU Max Frequency_0(MHz)": 2433.3333333333335,
            "CPU Requsted Frequency_0(MHz)": 1797.4166666666667,
            "Processor Power_0(Watt)": 2.5015000000000005,
            "Cumulative Processor Energy_0(Joules)": 3.141,
            "Cumulative Processor Energy_0(mWh)": 0.873,
            "IA Power_0(Watt)": 0.941,
            "Cumulative IA Energy_0(Joules)": 1.182,
            "Cumulative IA Energy_0(mWh)": 0.328,
            "Package Temperature_0(C)": 67.75,
            "Package Hot_0": 0.0,
            "CPU Min Temperature_0(C)": 66.5,
            "CPU Max Temperature_0(C)": 69.41666666666667,
            "DRAM Power_0(Watt)": 1.13675,
            "Cumulative DRAM Energy_0(Joules)": 1.426,
            "Cumulative DRAM Energy_0(mWh)": 0.396,
            "Package Power Limit_0(Watt)": 15.0,
            "GT Frequency(MHz)": 125.0,
            "GT Requsted Frequency(MHz)": 125.0,
        }

        with mock.patch.object(
            IntelPowerGadget, "_log_values", return_value=None
        ) as _, mock.patch.object(
            IntelPowerGadget, "_setup_cli", return_value=None
        ) as _:
            power_gadget = IntelPowerGadget(
                output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
                log_file_name="mock_intel_power_gadget_data.csv",
            )
            cpu_details = power_gadget.get_cpu_details()
            self.assertDictEqual(expected_cpu_details, cpu_details)
