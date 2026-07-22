import struct
import sys
import types
import unittest
from unittest import mock

from codecarbon.core import windows_emi
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
from codecarbon.external.hardware import CPU

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

    def test_snapshot_skips_unreadable_device(self, mock_channels, mock_paths):
        emi = self._make_emi()
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=OSError(
                31, "A device attached to the system is not functioning"
            ),
        ):
            emi.start()
            details = emi.get_cpu_details(Time(seconds=1))

        self.assertEqual(emi._last_measurements, {})
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


class _ValueRef:
    """Stand-in for a ctypes integer passed with byref()."""

    def __init__(self, value=0):
        self.value = value


def _make_fake_ctypes():
    fake = types.SimpleNamespace()
    fake.byref = lambda obj: obj
    fake.get_last_error = lambda: 5
    fake.FormatError = lambda error: "Access is denied."
    return fake


class TestListEmiDevicePaths(unittest.TestCase):
    """
    Exercise the device enumeration against fake cfgmgr32/ole32 libraries,
    so that the ctypes plumbing is tested on every platform.
    """

    MULTI_SZ = "\\\\?\\EMI0\x00\\\\?\\EMI1\x00\x00"

    def _patch(self, ole32, cfgmgr32, buffer=""):
        fake_ctypes = _make_fake_ctypes()
        fake_ctypes.create_unicode_buffer = lambda size: buffer
        return mock.patch.multiple(
            windows_emi,
            create=True,
            _IS_WINDOWS=True,
            ctypes=fake_ctypes,
            wintypes=types.SimpleNamespace(ULONG=_ValueRef),
            _GUID=mock.Mock,
            _ole32=ole32,
            _cfgmgr32=cfgmgr32,
        )

    def _make_cfgmgr32(self, size, size_cr=0, list_cr=0):
        cfgmgr32 = mock.Mock()

        def get_size(size_ref, guid_ref, _filter, _flags):
            size_ref.value = size
            return size_cr

        cfgmgr32.CM_Get_Device_Interface_List_SizeW.side_effect = get_size
        cfgmgr32.CM_Get_Device_Interface_ListW.return_value = list_cr
        return cfgmgr32

    def test_returns_empty_on_non_windows(self):
        with mock.patch.object(windows_emi, "_IS_WINDOWS", False):
            self.assertEqual(windows_emi.list_emi_device_paths(), [])

    def test_lists_present_devices(self):
        ole32 = mock.Mock()
        ole32.CLSIDFromString.return_value = 0
        cfgmgr32 = self._make_cfgmgr32(size=len(self.MULTI_SZ))
        with self._patch(ole32, cfgmgr32, buffer=self.MULTI_SZ):
            self.assertEqual(
                windows_emi.list_emi_device_paths(),
                ["\\\\?\\EMI0", "\\\\?\\EMI1"],
            )

    def test_returns_empty_when_guid_parsing_fails(self):
        ole32 = mock.Mock()
        ole32.CLSIDFromString.return_value = 0x800401F3  # CO_E_CLASSSTRING
        with self._patch(ole32, mock.Mock()):
            self.assertEqual(windows_emi.list_emi_device_paths(), [])

    def test_returns_empty_when_size_query_fails(self):
        ole32 = mock.Mock()
        ole32.CLSIDFromString.return_value = 0
        cfgmgr32 = self._make_cfgmgr32(size=0, size_cr=13)  # CR_FAILURE
        with self._patch(ole32, cfgmgr32):
            self.assertEqual(windows_emi.list_emi_device_paths(), [])

    def test_returns_empty_when_no_device_present(self):
        ole32 = mock.Mock()
        ole32.CLSIDFromString.return_value = 0
        # An empty interface list is reported as a single nul character
        cfgmgr32 = self._make_cfgmgr32(size=1)
        with self._patch(ole32, cfgmgr32):
            self.assertEqual(windows_emi.list_emi_device_paths(), [])

    def test_returns_empty_when_list_query_fails(self):
        ole32 = mock.Mock()
        ole32.CLSIDFromString.return_value = 0
        cfgmgr32 = self._make_cfgmgr32(size=len(self.MULTI_SZ), list_cr=13)
        with self._patch(ole32, cfgmgr32, buffer=self.MULTI_SZ):
            self.assertEqual(windows_emi.list_emi_device_paths(), [])


class TestEmiDeviceHandle(unittest.TestCase):
    """Exercise the CreateFile/DeviceIoControl wrapper against a fake kernel32."""

    def _patch(self, kernel32, string_buffer=None):
        fake_ctypes = _make_fake_ctypes()
        fake_ctypes.create_string_buffer = lambda size: string_buffer
        return mock.patch.multiple(
            windows_emi,
            create=True,
            ctypes=fake_ctypes,
            wintypes=types.SimpleNamespace(DWORD=_ValueRef),
            _kernel32=kernel32,
            _INVALID_HANDLE_VALUE=-1,
        )

    def test_opens_and_closes_the_device(self):
        kernel32 = mock.Mock()
        kernel32.CreateFileW.return_value = 42
        with self._patch(kernel32):
            with windows_emi._EmiDeviceHandle("dev0") as device:
                self.assertEqual(device._handle, 42)
            kernel32.CloseHandle.assert_called_once_with(42)

    def test_open_failure_raises_oserror(self):
        kernel32 = mock.Mock()
        kernel32.CreateFileW.return_value = -1
        with self._patch(kernel32):
            with self.assertRaises(OSError):
                windows_emi._EmiDeviceHandle("dev0").__enter__()
        kernel32.CloseHandle.assert_not_called()

    def test_ioctl_returns_output_buffer(self):
        payload = struct.pack("<H", EMI_VERSION_V2) + b"garbage"
        kernel32 = mock.Mock()
        kernel32.CreateFileW.return_value = 42

        def device_io_control(
            handle, code, _input, _input_size, output, output_size, returned, _ovl
        ):
            returned.value = 2
            return 1

        kernel32.DeviceIoControl.side_effect = device_io_control
        buffer = types.SimpleNamespace(raw=payload)
        with self._patch(kernel32, string_buffer=buffer):
            with windows_emi._EmiDeviceHandle("dev0") as device:
                result = device.ioctl(windows_emi.IOCTL_EMI_GET_VERSION, len(payload))
        self.assertEqual(result, struct.pack("<H", EMI_VERSION_V2))

    def test_ioctl_failure_raises_oserror(self):
        kernel32 = mock.Mock()
        kernel32.CreateFileW.return_value = 42
        kernel32.DeviceIoControl.return_value = 0
        buffer = types.SimpleNamespace(raw=b"")
        with self._patch(kernel32, string_buffer=buffer):
            with windows_emi._EmiDeviceHandle("dev0") as device:
                with self.assertRaises(OSError):
                    device.ioctl(windows_emi.IOCTL_EMI_GET_VERSION, 2)


def _fake_device_handle(responses):
    """Build an _EmiDeviceHandle replacement serving canned IOCTL responses."""

    class FakeHandle:
        def __init__(self, device_path):
            self.device_path = device_path

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def ioctl(self, code, output_size):
            return responses[code][:output_size]

    return FakeHandle


class TestReadDevice(unittest.TestCase):
    def test_read_device_channels(self):
        metadata = build_metadata_v2(CHANNELS)
        responses = {
            windows_emi.IOCTL_EMI_GET_VERSION: struct.pack("<H", EMI_VERSION_V2),
            windows_emi.IOCTL_EMI_GET_METADATA_SIZE: struct.pack("<L", len(metadata)),
            windows_emi.IOCTL_EMI_GET_METADATA: metadata,
        }
        with mock.patch.object(
            windows_emi, "_EmiDeviceHandle", _fake_device_handle(responses)
        ):
            self.assertEqual(windows_emi._read_device_channels("dev0"), CHANNELS)

    def test_read_device_measurements(self):
        responses = {
            windows_emi.IOCTL_EMI_GET_MEASUREMENT: build_measurements(
                [(100, 200), (300, 400)]
            )
        }
        with mock.patch.object(
            windows_emi, "_EmiDeviceHandle", _fake_device_handle(responses)
        ):
            self.assertEqual(
                windows_emi._read_device_measurements("dev0", 2),
                [(100, 200), (300, 400)],
            )


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

    def test_device_without_channels_is_skipped(self):
        with (
            mock.patch.object(sys, "platform", "win32"),
            mock.patch(
                "codecarbon.core.windows_emi.list_emi_device_paths",
                return_value=["dev0", "dev1"],
            ),
            mock.patch(
                "codecarbon.core.windows_emi._read_device_channels",
                side_effect=[[], CHANNELS],
            ),
        ):
            emi = WindowsEMI()
        self.assertEqual(emi._devices, [("dev1", CHANNELS, [0])])


@mock.patch("codecarbon.core.windows_emi.list_emi_device_paths", return_value=["dev0"])
@mock.patch("codecarbon.core.windows_emi._read_device_channels", return_value=CHANNELS)
@mock.patch.object(sys, "platform", "win32")
class TestWindowsEmiCpuHardware(unittest.TestCase):
    """The CPU hardware class wired on the windows_emi interface."""

    def test_measure_power_and_energy(self, mock_channels, mock_paths):
        cpu = CPU(output_dir="", mode="windows_emi", model=None, tdp=None)
        first = [(1_000, 0)] * 4
        # +2e9 pWh on the PKG channel over 2 seconds (2e7 * 100ns)
        second = [(2_000_001_000, 20_000_000)] * 4
        with mock.patch(
            "codecarbon.core.windows_emi._read_device_measurements",
            side_effect=[first, second],
        ):
            cpu.start()
            power, energy = cpu.measure_power_and_energy(last_duration=2)

        self.assertAlmostEqual(energy.kWh, 2e9 * 1e-15)
        self.assertAlmostEqual(power.W, 3.6)


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
