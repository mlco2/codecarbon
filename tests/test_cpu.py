import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import psutil
import pytest

from codecarbon.core.config import normalize_gpu_ids
from codecarbon.core.cpu import (
    DEFAULT_POWER_PER_CORE,
    TDP,
    IntelPowerGadget,
    IntelRAPL,
    _check_energy_file,
    _get_candidate_bases,
    _is_main_domain,
    _scan_base_for_rapl,
    _scan_direct_entries,
    _scan_domain_directories,
    is_powergadget_available,
    is_psutil_available,
    is_rapl_available,
)
from codecarbon.core.resource_tracker import ResourceTracker
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import count_physical_cpus
from codecarbon.external.hardware import CPU
from codecarbon.input import DataSource


class TestCPU(unittest.TestCase):
    @mock.patch("codecarbon.core.cpu.IntelPowerGadget", side_effect=Exception("boom"))
    def test_is_powergadget_available_returns_false_on_exception(
        self, mock_powergadget
    ):
        self.assertFalse(is_powergadget_available())

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

    @mock.patch("psutil.sensors_temperatures")
    def psutil_returns_expected_temperature(self, mock_cpu_times):
        mock_temp = mock.Mock()
        mock_temp.return_value = {"coretemp": 50, "k10temp": 50, "cpu_thermal": 50}
        self.assertEqual(psutil.sensors_temperatures(), 50)


class TestRAPLHelperFunctions(unittest.TestCase):
    def test_get_candidate_bases_for_custom_dir(self):
        with tempfile.TemporaryDirectory() as parent:
            rapl_dir = os.path.join(parent, "custom", "intel-rapl")
            os.makedirs(rapl_dir)

            result = _get_candidate_bases(rapl_dir)

        assert result == [rapl_dir, os.path.dirname(rapl_dir)]

    def test_get_candidate_bases_for_default_dir_deduplicates_and_filters(self):
        with mock.patch("codecarbon.core.cpu.os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path in {
                "/sys/class/powercap/intel-rapl/subsystem",
                "/sys/class/powercap/intel-rapl",
                "/sys/class/powercap",
            }

            result = _get_candidate_bases("/sys/class/powercap/intel-rapl/subsystem")

        assert result == [
            "/sys/class/powercap/intel-rapl/subsystem",
            "/sys/class/powercap/intel-rapl",
            "/sys/class/powercap",
        ]

    def test_is_main_domain_reads_package_name(self):
        with tempfile.TemporaryDirectory() as sub_path:
            with open(os.path.join(sub_path, "name"), "w") as f:
                f.write("package-0")

            assert _is_main_domain(sub_path, "intel-rapl:1") is True

    def test_is_main_domain_falls_back_to_suffix(self):
        with tempfile.TemporaryDirectory() as sub_path:
            assert _is_main_domain(sub_path, "intel-rapl:0") is True
            assert _is_main_domain(sub_path, "intel-rapl:1") is False

    def test_check_energy_file_warns_on_permission_denied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            energy_path = os.path.join(tmpdir, "energy_uj")
            with open(energy_path, "w") as f:
                f.write("1")
            warned = []

            with mock.patch("codecarbon.core.cpu.os.access", return_value=False):
                result = _check_energy_file(energy_path, True, warned.append)

        assert result is False
        assert warned == [energy_path]

    def test_scan_domain_directories_returns_true_for_main_domain(self):
        entry_path = "/tmp/entry"
        package_dir = "/tmp/entry/intel-rapl:0"

        with (
            mock.patch("codecarbon.core.cpu.os.listdir", return_value=["intel-rapl:0"]),
            mock.patch(
                "codecarbon.core.cpu.os.path.isdir",
                side_effect=lambda path: path.replace("\\", "/") == package_dir,
            ),
            mock.patch("codecarbon.core.cpu._is_main_domain", return_value=True),
            mock.patch("codecarbon.core.cpu._check_energy_file", return_value=True),
        ):
            assert _scan_domain_directories(entry_path, lambda _: None) is True

    def test_scan_direct_entries_returns_false_when_no_matching_dirs(self):
        with tempfile.TemporaryDirectory() as base:
            os.makedirs(os.path.join(base, "not-rapl"))

            assert _scan_direct_entries(base, lambda _: None) is False

    def test_scan_base_for_rapl_checks_direct_entries_fallback(self):
        with (
            mock.patch("codecarbon.core.cpu.os.listdir", return_value=["intel-rapl:0"]),
            mock.patch("codecarbon.core.cpu.os.path.isdir", return_value=False),
            mock.patch(
                "codecarbon.core.cpu._scan_domain_directories", return_value=False
            ),
            mock.patch("codecarbon.core.cpu._scan_direct_entries", return_value=True),
        ):
            assert _scan_base_for_rapl("/tmp/base", lambda _: None) is True

    @mock.patch("codecarbon.core.cpu._scan_base_for_rapl", side_effect=[False, True])
    @mock.patch("codecarbon.core.cpu._get_candidate_bases", return_value=["a", "b"])
    def test_is_rapl_available_scans_candidate_bases(self, mock_candidates, mock_scan):
        assert is_rapl_available("/tmp/custom") is True

    @mock.patch(
        "codecarbon.core.cpu._scan_base_for_rapl", side_effect=Exception("boom")
    )
    @mock.patch("codecarbon.core.cpu._get_candidate_bases", return_value=["a"])
    def test_is_rapl_available_returns_false_on_unexpected_error(
        self, mock_candidates, mock_scan
    ):
        assert is_rapl_available("/tmp/custom") is False


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

    def test_setup_cli_uses_windows_backup_when_primary_missing(self):
        with (
            mock.patch("codecarbon.core.cpu.sys.platform", "win32"),
            mock.patch.object(
                IntelPowerGadget,
                "_get_windows_exec_backup",
                lambda self: setattr(
                    self,
                    "_windows_exec_backup",
                    "C:\\Program Files\\Intel\\Power Gadget\\PowerLog3.0.exe",
                ),
            ),
            mock.patch(
                "codecarbon.core.cpu.shutil.which",
                side_effect=lambda path: None if path == "PowerLog3.0.exe" else path,
            ),
        ):
            gadget = IntelPowerGadget()

        self.assertEqual(
            gadget._cli,
            "C:\\Program Files\\Intel\\Power Gadget\\PowerLog3.0.exe",
        )

    def test_setup_cli_raises_on_unsupported_platform(self):
        with mock.patch("codecarbon.core.cpu.sys.platform", "linux"):
            with self.assertRaises(SystemError):
                IntelPowerGadget()

    def test_get_windows_exec_backup_finds_matching_folder(self):
        entries = [
            mock.Mock(is_dir=lambda: True, name="Other"),
            mock.Mock(is_dir=lambda: True, name="Power Gadget 3.7"),
        ]
        entries[0].name = "Other"
        entries[1].name = "Power Gadget 3.7"

        gadget = IntelPowerGadget.__new__(IntelPowerGadget)
        gadget._windows_exec = "PowerLog3.0.exe"

        with mock.patch("codecarbon.core.cpu.os.scandir", return_value=entries):
            gadget._get_windows_exec_backup()

        self.assertIn("Power Gadget 3.7", gadget._windows_exec_backup)

    def test_log_values_returns_none_on_unsupported_platform(self):
        gadget = IntelPowerGadget.__new__(IntelPowerGadget)
        gadget._system = "linux"

        self.assertIsNone(gadget._log_values())

    def test_log_values_warns_on_nonzero_returncode_windows(self):
        gadget = IntelPowerGadget.__new__(IntelPowerGadget)
        gadget._system = "win32"
        gadget._cli = "PowerLog3.0.exe"
        gadget._duration = 1
        gadget._resolution = 100
        gadget._log_file_path = "intel.csv"

        with (
            mock.patch(
                "codecarbon.core.cpu.subprocess.call", return_value=1
            ) as mock_call,
            mock.patch("codecarbon.core.cpu.logger.warning") as mock_warning,
        ):
            gadget._log_values()

        mock_call.assert_called_once()
        mock_warning.assert_called_once()

    @mock.patch("codecarbon.core.cpu.IntelPowerGadget._log_values")
    @mock.patch("codecarbon.core.cpu.pd.read_csv", side_effect=Exception("bad csv"))
    @mock.patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")
    def test_get_cpu_details_returns_empty_dict_on_read_error(
        self, mock_setup, mock_read_csv, mock_log_values
    ):
        gadget = IntelPowerGadget()

        self.assertEqual(gadget.get_cpu_details(), {})


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

    def test_main_fallback_default_power_when_unknown_cpu(self):
        with (
            mock.patch(
                "codecarbon.core.cpu.detect_cpu_model", return_value="Mystery CPU"
            ),
            mock.patch(
                "codecarbon.core.cpu.TDP._get_cpu_power_from_registry",
                return_value=None,
            ),
            mock.patch("codecarbon.core.cpu.is_psutil_available", return_value=True),
            mock.patch("codecarbon.core.cpu.count_cpus", return_value=8),
        ):
            tdp = TDP()

        self.assertEqual(tdp.model, "Mystery CPU")
        self.assertEqual(tdp.tdp, 8 * DEFAULT_POWER_PER_CORE)


class TestResourceTrackerCPUTracking(unittest.TestCase):
    def test_set_cpu_tracking_skips_tdp_when_rapl_available(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {"cpu_physical_count": 1}
                self._force_cpu_power = None
                self._output_dir = ""
                self._rapl_include_dram = False
                self._rapl_prefer_psys = False
                self._tracking_mode = "machine"
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)
        cpu_device = mock.Mock()
        cpu_device.get_model.return_value = "Mock CPU"

        with (
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.TDP",
                side_effect=AssertionError(
                    "TDP should not be instantiated when RAPL is active"
                ),
            ) as mocked_tdp,
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_rapl_available",
                return_value=True,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.CPU.from_utils",
                return_value=cpu_device,
            ) as mocked_from_utils,
        ):
            resource_tracker.set_CPU_tracking()

        mocked_tdp.assert_not_called()
        mocked_from_utils.assert_called_once_with(
            output_dir=tracker._output_dir,
            mode="intel_rapl",
            rapl_include_dram=tracker._rapl_include_dram,
            rapl_prefer_psys=tracker._rapl_prefer_psys,
        )
        self.assertEqual(resource_tracker.cpu_tracker, "RAPL")
        self.assertEqual(tracker._conf["cpu_model"], "Mock CPU")

    def test_set_cpu_tracking_force_cpu_load_instantiates_tdp(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {"cpu_physical_count": 2, "force_mode_cpu_load": True}
                self._force_cpu_power = None
                self._output_dir = ""
                self._rapl_include_dram = False
                self._rapl_prefer_psys = False
                self._tracking_mode = "machine"
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)
        fake_tdp = mock.Mock()
        fake_tdp.tdp = 50
        fake_tdp.model = "Mock CPU"

        with (
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.TDP", return_value=fake_tdp
            ) as mocked_tdp,
            mock.patch(
                "codecarbon.core.resource_tracker.ResourceTracker._setup_cpu_load_mode",
                return_value=True,
            ) as mocked_setup_cpu_load,
            mock.patch(
                "codecarbon.core.resource_tracker.ResourceTracker._setup_fallback_tracking"
            ) as mocked_fallback,
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_rapl_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
                return_value=False,
            ),
        ):
            resource_tracker.set_CPU_tracking()

        mocked_tdp.assert_called_once_with()
        mocked_setup_cpu_load.assert_called_once_with(fake_tdp, 100)
        mocked_fallback.assert_not_called()

    def test_set_cpu_tracking_fallback_instantiates_tdp(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {"cpu_physical_count": 4}
                self._force_cpu_power = None
                self._output_dir = ""
                self._rapl_include_dram = False
                self._rapl_prefer_psys = False
                self._tracking_mode = "machine"
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)
        fake_tdp = mock.Mock()
        fake_tdp.tdp = 20
        fake_tdp.model = "Mock CPU"

        with (
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.TDP", return_value=fake_tdp
            ) as mocked_tdp,
            mock.patch(
                "codecarbon.core.resource_tracker.ResourceTracker._setup_fallback_tracking"
            ) as mocked_fallback,
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.cpu.is_rapl_available",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
                return_value=False,
            ),
        ):
            resource_tracker.set_CPU_tracking()

        mocked_tdp.assert_called_once_with()
        mocked_fallback.assert_called_once_with(fake_tdp, 80)


class TestResourceTrackerGPUTracking(unittest.TestCase):
    def test_normalize_gpu_ids_mixed_list_with_escaping(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {}
                self._gpu_ids = [0, "MIG-f1e$%^", "1, 2", "GPU-abcd!"]
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)

        normalized_gpu_ids = normalize_gpu_ids(resource_tracker.tracker._gpu_ids)

        self.assertEqual(normalized_gpu_ids, [0, "MIG-f1e", "1", "2", "GPU-abcd"])

    def test_normalize_gpu_ids_mixed_list_ignores_invalid_entries(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {}
                self._gpu_ids = [0, {"invalid": "entry"}, "GPU-123"]
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)

        normalized_gpu_ids = normalize_gpu_ids(resource_tracker.tracker._gpu_ids)

        self.assertEqual(normalized_gpu_ids, [0, "GPU-123"])

    def test_set_gpu_tracking_rocm_with_string_ids(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {}
                self._gpu_ids = "0,1"
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)
        fake_devices = mock.Mock()
        fake_devices.devices.get_gpu_static_info.return_value = [
            {"name": "AMD Instinct MI300X"},
            {"name": "AMD Instinct MI300X"},
        ]

        with (
            mock.patch(
                "codecarbon.core.resource_tracker.normalize_gpu_ids",
                return_value=[0, 1],
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.gpu.is_nvidia_system",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.gpu.is_rocm_system",
                return_value=True,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.GPU.from_utils",
                return_value=fake_devices,
            ),
        ):
            resource_tracker.set_GPU_tracking()

        self.assertEqual(tracker._gpu_ids, [0, 1])
        self.assertEqual(tracker._conf["gpu_ids"], [0, 1])
        self.assertEqual(tracker._conf["gpu_count"], 2)
        self.assertEqual(resource_tracker.gpu_tracker, "amdsmi")
        self.assertEqual(tracker._conf["gpu_model"], "2 x AMD Instinct MI300X")
        self.assertEqual(tracker._hardware, [fake_devices])

    def test_set_gpu_tracking_rocm_with_mixed_ids(self):
        class DummyTracker:
            def __init__(self):
                self._conf = {}
                self._gpu_ids = [0, "MIG-f1e$%^", "1, 2"]
                self._hardware = []

        tracker = DummyTracker()
        resource_tracker = ResourceTracker(tracker)
        fake_devices = mock.Mock()
        fake_devices.devices.get_gpu_static_info.return_value = [
            {"name": "AMD Instinct MI300X"},
            {"name": "AMD Instinct MI300X"},
        ]

        with (
            mock.patch(
                "codecarbon.core.resource_tracker.gpu.is_nvidia_system",
                return_value=False,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.gpu.is_rocm_system",
                return_value=True,
            ),
            mock.patch(
                "codecarbon.core.resource_tracker.GPU.from_utils",
                return_value=fake_devices,
            ) as mocked_gpu_from_utils,
        ):
            resource_tracker.set_GPU_tracking()

        expected_gpu_ids = [0, "MIG-f1e", "1", "2"]
        mocked_gpu_from_utils.assert_called_once_with(expected_gpu_ids)
        self.assertEqual(tracker._gpu_ids, expected_gpu_ids)
        self.assertEqual(tracker._conf["gpu_ids"], expected_gpu_ids)
        self.assertEqual(tracker._conf["gpu_count"], 2)


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
