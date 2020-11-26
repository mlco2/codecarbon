import os
import unittest
from unittest import mock

import pytest

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL


class TestIntelPowerGadget(unittest.TestCase):
    @pytest.mark.integ_test
    def test_intel_power_gadget(self):
        power_gadget = IntelPowerGadget()
        cpu_details = power_gadget.get_cpu_details()
        assert len(cpu_details) > 0

    @mock.patch("codecarbon.core.cpu.IntelPowerGadget._log_values")
    @mock.patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")
    def test_get_cpu_details(self, mock_setup, mock_log_values):
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

        power_gadget = IntelPowerGadget(
            output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
            log_file_name="mock_intel_power_gadget_data.csv",
        )
        cpu_details = power_gadget.get_cpu_details()
        self.assertDictEqual(expected_cpu_details, cpu_details)


class TestIntelRAPL(unittest.TestCase):
    @mock.patch(
        "codecarbon.core.cpu.IntelRAPL._is_platform_supported",
        return_value=True,
    )
    def test_intel_rapl(self, mock_platform):
        expected_cpu_details = {"Processor Power_0(Watt)": 0.0, "psys": 0.0}

        rapl = IntelRAPL(
            rapl_dir=os.path.join(os.path.dirname(__file__), "test_data", "rapl")
        )
        self.assertDictEqual(expected_cpu_details, rapl.get_cpu_details())
