import os
import subprocess
import sys
import unittest
from unittest import mock

import pytest

from codecarbon.core.cpu import (
    TDP,
    IntelPowerGadget,
    IntelRAPL,
    is_powergadget_available,
    is_psutil_available,
)
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import count_physical_cpus
from codecarbon.external.hardware import CPU
from codecarbon.input import DataSource


class TestCPU(unittest.TestCase):
    @mock.patch("psutil.cpu_times")
    def test_is_psutil_available_with_nice(self, mock_cpu_times):
        # Create a mock with 'nice' attribute
        mock_times = mock.Mock()
        mock_times.nice = 0.1
        mock_cpu_times.return_value = mock_times
        self.assertTrue(is_psutil_available())

    @mock.patch("psutil.cpu_times")
    def test_is_psutil_available_with_small_nice(self, mock_cpu_times):
        # Test when nice attribute is too small
        mock_times = mock.Mock()
        mock_times.nice = 0.00001
        mock_cpu_times.return_value = mock_times
        self.assertFalse(is_psutil_available())

    @mock.patch("psutil.cpu_times")
    def test_is_psutil_available_without_nice(self, mock_cpu_times):
        # Create a mock without 'nice' attribute (like Windows)
        mock_times = mock.Mock(spec=[])  # Empty spec = no attributes
        mock_cpu_times.return_value = mock_times
        with mock.patch("psutil.cpu_percent") as mock_cpu_percent:
            self.assertTrue(is_psutil_available())
            mock_cpu_percent.assert_called_once_with(interval=0.0, percpu=False)

    @mock.patch("psutil.cpu_times", side_effect=Exception("Test error"))
    def test_is_psutil_not_available_on_exception(self, mock_cpu_times):
        self.assertFalse(is_psutil_available())


class TestIntelPowerGadget(unittest.TestCase):
    @pytest.mark.integ_test
    def test_intel_power_gadget(self):
        if is_powergadget_available():
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
        if is_powergadget_available():
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
            # Create proper RAPL hierarchy: rapl_dir/intel-rapl/intel-rapl:N/
            provider_dir = os.path.join(self.rapl_dir, "intel-rapl")
            os.makedirs(os.path.join(provider_dir, "intel-rapl:0"), exist_ok=True)
            with open(os.path.join(provider_dir, "intel-rapl:0/name"), "w") as f:
                f.write("package-0")
            with open(os.path.join(provider_dir, "intel-rapl:0/energy_uj"), "w") as f:
                f.write("52649883221")
            with open(
                os.path.join(provider_dir, "intel-rapl:0/max_energy_range_uj"), "w"
            ) as f:
                f.write("262143328850")

            os.makedirs(os.path.join(provider_dir, "intel-rapl:1"), exist_ok=True)
            with open(os.path.join(provider_dir, "intel-rapl:1/name"), "w") as f:
                f.write("psys")
            with open(os.path.join(provider_dir, "intel-rapl:1/energy_uj"), "w") as f:
                f.write("117870082040")
            with open(
                os.path.join(provider_dir, "intel-rapl:1/max_energy_range_uj"), "w"
            ) as f:
                f.write("262143328850")

    @unittest.skipUnless(sys.platform.lower().startswith("lin"), "requires Linux")
    def test_intel_rapl(self):
        # The new RAPL implementation prioritizes package domains over psys
        # because package domains are more reliable and update correctly under load.
        # When both package and psys are available, only package is used.
        expected_cpu_details = {
            "Processor Energy Delta_0(kWh)": 0.0,
            "Processor Power Delta_0(kWh)": 0.0,
        }

        rapl = IntelRAPL(rapl_dir=self.rapl_dir)
        self.assertDictEqual(
            expected_cpu_details, rapl.get_cpu_details(duration=Time(0))
        )

    @unittest.skipUnless(sys.platform.lower().startswith("lin"), "requires Linux")
    def test_rapl_cpu_hardware(self):
        cpu = CPU(
            output_dir="",
            mode="intel_rapl",
            model=None,
            tdp=None,
            rapl_dir=self.rapl_dir,
        )
        expected_energy = Energy(0)
        expected_power = Power(0)
        assert expected_power, expected_energy == cpu.measure_power_and_energy(
            last_duration=0.01
        )


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

        # ======= WORKING AS EXPECTED ========

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

        # Match although have a missing part
        model = "AMD Ryzen 1950"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950",
        )

        # Match although have lot of missing parts
        model = "5800K"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD A10-5800K",
        )

        # Match although have a missing part (tricky!)
        model = "AMD Ryzen 1950x"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950X",
        )

        # Match although (noisy) parts are added
        model = "AMD Ryzen Threadripper 1950 16-Core Processor"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950",
        )

        # Match although (noisy) parts are added (tricky again!)
        model = "AMD Ryzen Threadripper 1950X 16-Core Processor"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD Ryzen Threadripper 1950X",
        )

        # Match although many (noisy) parts are added
        model = "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "Intel Core i7-8850H",
        )

        model = "Intel(R) Xeon(R) Gold 6330N CPU @ 2.20Ghz"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "Intel Xeon Gold 6330N",
        )
        model = "Intel(R) Xeon(R) Silver 4208 CPU @ 2.10GHz"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "Intel Xeon Silver 4208",
        )
        model = "Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "Intel Xeon E5-2620 v3",
        )
        # Does not match when missing part replaced by (here wrong) other part.
        # Which here is good. Could happen if Intel creates a model with the
        # same name than AMD ("5800K"), but only AMD exists in our cpu list.
        model = "Intel 5800K"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )

        # ======= LIMITS ========

        # LIMIT 1a:
        # The following matches with many "AMD Ryzen 3 [...]" models.
        # Should return None in non-greedy mode
        model = "AMD Ryzen 3"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )

        # In greedy mode: should return the first model that contains the
        # same words from the cpu list.
        model = "AMD Ryzen 3"
        self.assertRegex(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
            r"AMD Ryzen 3.*",
        )

        # LIMIT 1b:
        # Since the following matches many models with varying tdps
        # In non-greedy mode: should return None.
        model = "AMD Ryzen PRO 3"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )

        # In greedy mode: should return the first model that contains the
        # same words from the cpu list.
        model = "AMD Ryzen PRO 3"
        self.assertRegex(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
            r"AMD Ryzen 3 PRO.*",
        )

        # LIMIT 2:
        # "AMD Ryzen 3 1200 PRO" matches with both:
        # - "AMD Ryzen 3 1200"
        # - "AMD Ryzen 3 PRO 1200"
        # We would expect it to only match with "AMD Ryzen 3 PRO 1200".
        # In non-greedy mode: should return None.
        model = "AMD Ryzen 3 1200 PRO"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )

        # In greedy mode: should return the first model that contains almost
        # all the same words from the cpu list.
        model = "AMD Ryzen 3 1200 PRO"
        self.assertRegex(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
            r"AMD Ryzen 3.*1200",
        )

        # LIMIT 3:
        # Letter missing from a word (instead of "AMD A10-4600M")
        # Returns None since the ratio/score is below 100 (with threshold 100).
        model = "AMD A10-4600"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=True),
        )

        # However, "A10" and "4600" are considered two separate words when
        # tokenized. In this case there is no issue.
        model = "AMD 4600M"
        self.assertEqual(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
            "AMD A10-4600M",
        )

        # LIMIT 4:
        # Wrong letter from a word (instead of "AMD A10-4600M")
        # Returns None since the ratio/score is below 100 (with threshold 100).
        model = "AMD A10-4650M"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )

        # LIMIT 5:
        # Does not match when both a missing part and an additional part.
        # Which here is bad.
        model = "AMD Threadripper 1950X 16-Core Processor"
        self.assertIsNone(
            tdp._get_matching_cpu(model, cpu_data, greedy=False),
        )


class TestPhysicalCPU(unittest.TestCase):
    def test_count_physical_cpus_windows(self):
        with mock.patch("platform.system", return_value="Windows"):

            with mock.patch(
                "subprocess.run", return_value=mock.Mock(returncode=0, stdout="4")
            ):
                assert count_physical_cpus() == 4

            with mock.patch(
                "subprocess.run", return_value=mock.Mock(returncode=0, stdout="")
            ):
                assert count_physical_cpus() == 1

    def test_count_physical_cpus_windows_with_error(self):
        with mock.patch("platform.system", return_value="Windows"):
            # Test CalledProcessError
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "powershell"),
            ):
                assert count_physical_cpus() == 1

            # Test TimeoutExpired
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired("powershell", 10),
            ):
                assert count_physical_cpus() == 1

            # Test ValueError when converting invalid output
            with mock.patch(
                "subprocess.run", return_value=mock.Mock(returncode=0, stdout="invalid")
            ):
                assert count_physical_cpus() == 1

    def test_count_physical_cpus_linux(self):
        with mock.patch("platform.system", return_value="Linux"):
            lscpu_output = "Socket(s): 2\n"
            with mock.patch("subprocess.check_output", return_value=lscpu_output):
                assert count_physical_cpus() == 2

            lscpu_output = "Some other output\n"
            with mock.patch("subprocess.check_output", return_value=lscpu_output):
                assert count_physical_cpus() == 1

            with mock.patch(
                "subprocess.check_output",
                side_effect=subprocess.CalledProcessError(1, "lscpu"),
            ):
                assert count_physical_cpus() == 1
