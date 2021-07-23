import os
import sys
import unittest
from unittest import mock

import pytest

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL, TDP
from codecarbon.input import DataSource


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
        cpu_details["Cumulative IA Energy_0(mWh)"] = round(
            cpu_details["Cumulative IA Energy_0(mWh)"], 3
        )
        self.assertDictEqual(expected_cpu_details, cpu_details)


class TestIntelRAPL(unittest.TestCase):
    def setUp(self) -> None:
        self.rapl_dir = os.path.join(os.path.dirname(__file__), "test_data", "rapl")
        if sys.platform.lower().startswith("lin"):
            os.makedirs(os.path.join(self.rapl_dir, "intel-rapl:0"), exist_ok=True)
            with open(os.path.join(self.rapl_dir, "intel-rapl:0/name"), "w") as f:
                f.write("package-0")
            with open(os.path.join(self.rapl_dir, "intel-rapl:0/energy_uj"), "w") as f:
                f.write("52649883221")

            os.makedirs(os.path.join(self.rapl_dir, "intel-rapl:1"), exist_ok=True)
            with open(os.path.join(self.rapl_dir, "intel-rapl:1/name"), "w") as f:
                f.write("psys")
            with open(os.path.join(self.rapl_dir, "intel-rapl:1/energy_uj"), "w") as f:
                f.write("117870082040")

    @unittest.skipUnless(sys.platform.lower().startswith("lin"), "requires Linux")
    def test_intel_rapl(self):
        expected_cpu_details = {"Processor Power_0(Watt)": 0.0, "psys": 0.0}

        rapl = IntelRAPL(
            rapl_dir=os.path.join(os.path.dirname(__file__), "test_data", "rapl")
        )
        self.assertDictEqual(expected_cpu_details, rapl.get_cpu_details())



class TestTDP(unittest.TestCase):
    def test_get_cpu_power_from_registry(self):
        tdp = TDP()
        model = "Intel Core i7-8850H"
        self.assertEqual(tdp._get_cpu_power_from_registry(model), 45)
        model = "AMD Ryzen Threadripper 1950X"
        self.assertEqual(tdp._get_cpu_power_from_registry(model), 180)
        model = "AMD Ryzen Threadripper 1950X 16-Core Processor"
        self.assertEqual(tdp._get_cpu_power_from_registry(model), 180)


    def test_get_matching_cpu(self):
        tdp = TDP()
        cpu_data = DataSource().get_cpu_power_data()

        # The following matches many models with varying tdps.
        # Should return None in non greedy mode.
        model = "AMD Ryzen PRO 3"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            None,
        )

        # And should return the first model found in the list in greedy mode.
        model = "AMD Ryzen PRO 3"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
            "AMD Ryzen 3 PRO 1200",
        )

        # Exact match
        model = "AMD Ryzen 3 1200"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen 3 1200",
        )

        # Exact match with varying case
        model = "amd ryzen 3 1200"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen 3 1200",
        )

        # Should find the correct model and version even though a part is
        # missing
        model = "AMD Ryzen 1950"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950",
        )

        model = "AMD Ryzen 1950x"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950X",
        )

        # Should find the correct model and version even though parts are
        # added (noise)
        model = "AMD Ryzen Threadripper 1950 16-Core Processor"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950",
        )

        model = "AMD Ryzen Threadripper 1950X 16-Core Processor"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950X",
        )

        # Should find the model even though many parts are added (large noise)
        model = "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "Intel Core i7-8850H",
        )

        # The following matches with many "AMD Ryzen 3 ..." models.
        # Should return None in non greedy mode
        model = "AMD Ryzen 3"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            None,
        )

        # /! LIMIT !\ The following matches with both:
        # "AMD Ryzen 3 1200", and "AMD Ryzen 3 PRO 1200"
        # However, it should only match with AMD Ryzen 3 PRO 1200
        # (the words are in reversed order)

        # model = "AMD Ryzen 3 1200 PRO"
        # self.assertEqual(
        #     tdp._get_matching_cpu(model, cpu_data, greedy=False),
        #     "AMD Ryzen 3 PRO 1200",
        # )

        # Compensates for the previous test failure using greedy mode
        model = "AMD Ryzen 3 1200 PRO"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
            "AMD Ryzen 3 1200",
        )
