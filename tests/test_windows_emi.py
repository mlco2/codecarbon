import struct
import sys
import unittest
from unittest import mock

from codecarbon.core.units import Time
from codecarbon.core.windows_emi import (
    EMI_VERSION_V1,
    EMI_VERSION_V2,
    WindowsEMI,
    clear_emi_cache,
    is_emi_available,
    parse_channel_names,
    parse_measurements,
    select_channel_indices,
)

CHANNELS = [
    "RAPL_Package0_PKG",
    "RAPL_Package0_DRAM",
    "RAPL_Package0_PP0",
    "RAPL_Package0_PP1",
]


def build_metadata_v2(channel_names):
    metadata = "Microsoft".encode("utf-16-le").ljust(32, b"\x00")
    metadata += "PPM".encode("utf-16-le").ljust(32, b"\x00")
    metadata += struct.pack("<HH", 1, len(channel_names))
    for name in channel_names:
        raw = name.encode("utf-16-le") + b"\x00\x00"
        metadata += struct.pack("<iH", 0, len(raw)) + raw
    return metadata


def build_metadata_v1(name):
    metadata = struct.pack("<i", 0)
    metadata += "OEM".encode("utf-16-le").ljust(32, b"\x00")
    metadata += "Model".encode("utf-16-le").ljust(32, b"\x00")
    raw = name.encode("utf-16-le") + b"\x00\x00"
    metadata += struct.pack("<HH", 1, len(raw))
    metadata += raw
    return metadata


def build_measurements(values):
    # values: list of (absolute_energy_pwh, absolute_time_100ns)
    return b"".join(struct.pack("<QQ", energy, time) for energy, time in values)


class TestEmiParsing(unittest.TestCase):
    def test_parse_channel_names_v2(self):
        metadata = build_metadata_v2(CHANNELS)
        self.assertEqual(parse_channel_names(EMI_VERSION_V2, metadata), CHANNELS)

    def test_parse_channel_names_v1(self):
        metadata = build_metadata_v1("CPU Meter")
        self.assertEqual(parse_channel_names(EMI_VERSION_V1, metadata), ["CPU Meter"])

    def test_parse_channel_names_unknown_version(self):
        with self.assertRaises(ValueError):
            parse_channel_names(3, b"")

    def test_parse_measurements(self):
        raw = build_measurements([(100, 200), (300, 400)])
        self.assertEqual(parse_measurements(raw), [(100, 200), (300, 400)])


class TestEmiChannelSelection(unittest.TestCase):
    def test_selects_package_channel_only(self):
        self.assertEqual(select_channel_indices(CHANNELS), [0])

    def test_selects_dram_when_requested(self):
        self.assertEqual(select_channel_indices(CHANNELS, include_dram=True), [0, 1])

    def test_single_unknown_channel_is_used(self):
        self.assertEqual(select_channel_indices(["CPU Meter"]), [0])

    def test_no_package_channel_uses_all(self):
        self.assertEqual(select_channel_indices(["a", "b"]), [0, 1])

    def test_multiple_packages(self):
        names = ["RAPL_Package0_PKG", "RAPL_Package1_PKG", "RAPL_Package0_PP0"]
        self.assertEqual(select_channel_indices(names), [0, 1])


@mock.patch("codecarbon.core.windows_emi.list_emi_device_paths", return_value=["dev0"])
@mock.patch("codecarbon.core.windows_emi._read_device_channels", return_value=CHANNELS)
@mock.patch.object(sys, "platform", "win32")
class TestWindowsEMI(unittest.TestCase):
    def _make_emi(self, **kwargs):
        return WindowsEMI(**kwargs)

    def test_setup_selects_package_channel(self, mock_channels, mock_paths):
        emi = self._make_emi()
        self.assertEqual(emi._devices, [("dev0", CHANNELS, [0])])

    def test_get_cpu_details_computes_energy_and_power(self, mock_channels, mock_paths):
        emi = self._make_emi()
        first = [(1_000, 0)] * 4
        # +2e9 pWh on the PKG channel over 2 seconds (2e7 * 100ns)
        second = [(2_000_001_000, 20_000_000)] * 4
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=[first, second],
        ):
            emi.start()
            details = emi.get_cpu_details(Time(seconds=2))

        self.assertAlmostEqual(details["Processor Energy Delta_0(kWh)"], 2e9 * 1e-15)
        self.assertAlmostEqual(details["Processor Power Delta_0(kWh)"], 3.6)
        self.assertEqual(emi.get_static_cpu_details(), details)

    def test_get_cpu_details_uses_duration_when_time_delta_is_zero(
        self, mock_channels, mock_paths
    ):
        emi = self._make_emi()
        first = [(0, 500)] * 4
        second = [(1_000_000_000, 500)] * 4
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=[first, second],
        ):
            emi.start()
            details = emi.get_cpu_details(Time(seconds=1))

        self.assertAlmostEqual(details["Processor Power Delta_0(kWh)"], 3.6)

    def test_get_cpu_details_skips_negative_delta(self, mock_channels, mock_paths):
        emi = self._make_emi()
        first = [(5_000, 0)] * 4
        second = [(1_000, 10_000_000)] * 4  # counter went backwards
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=[first, second],
        ):
            emi.start()
            details = emi.get_cpu_details(Time(seconds=1))

        self.assertEqual(details["Processor Energy Delta_0(kWh)"], 0.0)
        self.assertEqual(details["Processor Power Delta_0(kWh)"], 0.0)

    def test_include_dram_channel(self, mock_channels, mock_paths):
        emi = self._make_emi(emi_include_dram=True)
        self.assertEqual(emi._devices, [("dev0", CHANNELS, [0, 1])])
        first = [(0, 0)] * 4
        second = [(1_000_000, 10_000_000)] * 4
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=[first, second],
        ):
            emi.start()
            details = emi.get_cpu_details(Time(seconds=1))

        self.assertIn("Processor Energy Delta_0(kWh)", details)
        self.assertIn("Processor Energy Delta_1(kWh)", details)


class TestWindowsEMISetupErrors(unittest.TestCase):
    def test_not_supported_on_other_platforms(self):
        with mock.patch.object(sys, "platform", "linux"):
            with self.assertRaises(SystemError):
                WindowsEMI()

    def test_no_device_found(self):
        with (
            mock.patch.object(sys, "platform", "win32"),
            mock.patch(
                "codecarbon.core.windows_emi.list_emi_device_paths", return_value=[]
            ),
        ):
            with self.assertRaises(FileNotFoundError):
                WindowsEMI()

    def test_unreadable_device_metadata(self):
        with (
            mock.patch.object(sys, "platform", "win32"),
            mock.patch(
                "codecarbon.core.windows_emi.list_emi_device_paths",
                return_value=["dev0"],
            ),
            mock.patch(
                "codecarbon.core.windows_emi._read_device_channels",
                side_effect=OSError(5, "Access is denied."),
            ),
        ):
            with self.assertRaises(FileNotFoundError):
                WindowsEMI()


class TestIsEmiAvailable(unittest.TestCase):
    def setUp(self):
        clear_emi_cache()

    def tearDown(self):
        clear_emi_cache()

    def test_false_on_non_windows(self):
        with mock.patch("codecarbon.core.windows_emi._IS_WINDOWS", False):
            self.assertFalse(is_emi_available())

    def test_true_when_snapshot_readable(self):
        emi = mock.Mock()
        emi._snapshot.return_value = {("dev0", 0): (1, 1)}
        with (
            mock.patch("codecarbon.core.windows_emi._IS_WINDOWS", True),
            mock.patch("codecarbon.core.windows_emi.WindowsEMI", return_value=emi),
        ):
            self.assertTrue(is_emi_available())

    def test_false_when_no_measurement(self):
        emi = mock.Mock()
        emi._snapshot.return_value = {}
        with (
            mock.patch("codecarbon.core.windows_emi._IS_WINDOWS", True),
            mock.patch("codecarbon.core.windows_emi.WindowsEMI", return_value=emi),
        ):
            self.assertFalse(is_emi_available())

    def test_false_on_exception(self):
        with (
            mock.patch("codecarbon.core.windows_emi._IS_WINDOWS", True),
            mock.patch(
                "codecarbon.core.windows_emi.WindowsEMI",
                side_effect=FileNotFoundError("no device"),
            ),
        ):
            self.assertFalse(is_emi_available())


if __name__ == "__main__":
    unittest.main()
