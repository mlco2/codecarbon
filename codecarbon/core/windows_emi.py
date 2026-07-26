"""
Implements tracking CPU power consumption on Windows using the built-in
Energy Meter Interface (EMI).

Since Windows 11, the OS kernel exposes the CPU RAPL energy counters
(the same MSR-based counters read from /sys/class/powercap on Linux)
through a standard device interface, for both Intel and AMD CPUs.
No third-party driver, no admin rights and no extra dependency needed.
On Windows 10, EMI only reports on devices with dedicated metering
hardware (e.g. Surface Book).

https://learn.microsoft.com/en-us/windows-hardware/drivers/powermeter/energy-meter-interface
"""

from __future__ import annotations

import struct
import sys
from functools import lru_cache
from typing import Dict, List, Tuple

from codecarbon.core.units import Time
from codecarbon.external.logger import logger

# From emi.h: CTL_CODE(FILE_DEVICE_UNKNOWN, fn, METHOD_BUFFERED, FILE_READ_ACCESS)
#   = (0x22 << 16) | (1 << 14) | (fn << 2) | 0
IOCTL_EMI_GET_VERSION = 0x224000
IOCTL_EMI_GET_METADATA_SIZE = 0x224004
IOCTL_EMI_GET_METADATA = 0x224008
IOCTL_EMI_GET_MEASUREMENT = 0x22400C

EMI_VERSION_V1 = 1
EMI_VERSION_V2 = 2

# Size of EMI_CHANNEL_MEASUREMENT_DATA {ULONGLONG AbsoluteEnergy; ULONGLONG AbsoluteTime;}
EMI_MEASUREMENT_SIZE = 16

GUID_DEVICE_ENERGY_METER = "{45BD8344-7ED6-49CF-A440-C276C933B053}"

# AbsoluteEnergy is in picowatt-hours, AbsoluteTime in 100ns units
PWH_TO_KWH = 1e-15
PWH_TO_WH = 1e-12
HNS_TO_S = 1e-7

# Maximum relative difference between two absolute energy counters for them to
# be considered two views of the same hardware counter.
MIRRORED_CHANNEL_TOLERANCE = 1e-6

_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x1
_FILE_SHARE_WRITE = 0x2
_OPEN_EXISTING = 3
_CR_SUCCESS = 0
_CM_GET_DEVICE_INTERFACE_LIST_PRESENT = 0

_IS_WINDOWS = sys.platform.startswith("win")

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _cfgmgr32 = ctypes.WinDLL("cfgmgr32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ole32 = ctypes.WinDLL("ole32", use_last_error=True)

    class _GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _kernel32.DeviceIoControl.restype = wintypes.BOOL
    _kernel32.DeviceIoControl.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    _INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def list_emi_device_paths() -> List[str]:
    """
    Enumerate the device interface paths of all present energy meters.
    """
    if not _IS_WINDOWS:
        return []
    guid = _GUID()
    if _ole32.CLSIDFromString(GUID_DEVICE_ENERGY_METER, ctypes.byref(guid)) != 0:
        return []
    size = wintypes.ULONG(0)
    cr = _cfgmgr32.CM_Get_Device_Interface_List_SizeW(
        ctypes.byref(size),
        ctypes.byref(guid),
        None,
        _CM_GET_DEVICE_INTERFACE_LIST_PRESENT,
    )
    if cr != _CR_SUCCESS or size.value <= 1:
        return []
    buffer = ctypes.create_unicode_buffer(size.value)
    cr = _cfgmgr32.CM_Get_Device_Interface_ListW(
        ctypes.byref(guid),
        None,
        buffer,
        size,
        _CM_GET_DEVICE_INTERFACE_LIST_PRESENT,
    )
    if cr != _CR_SUCCESS:
        return []
    # The buffer holds a REG_MULTI_SZ-style list of nul-terminated strings
    paths = []
    current: List[str] = []
    for char in buffer[: size.value]:
        if char == "\x00":
            if current:
                paths.append("".join(current))
                current = []
        else:
            current.append(char)
    return paths


class _EmiDeviceHandle:
    """Context manager around a CreateFile handle on an EMI device."""

    def __init__(self, device_path: str):
        self._device_path = device_path
        self._handle = None

    def __enter__(self):
        handle = _kernel32.CreateFileW(
            self._device_path,
            _GENERIC_READ,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE,
            None,
            _OPEN_EXISTING,
            0,
            None,
        )
        if handle is None or handle == _INVALID_HANDLE_VALUE:
            error = ctypes.get_last_error()
            raise OSError(error, ctypes.FormatError(error), self._device_path)
        self._handle = handle
        return self

    def __exit__(self, *exc_info):
        if self._handle is not None:
            _kernel32.CloseHandle(self._handle)
            self._handle = None

    def ioctl(self, code: int, output_size: int) -> bytes:
        output = ctypes.create_string_buffer(output_size)
        returned = wintypes.DWORD(0)
        ok = _kernel32.DeviceIoControl(
            self._handle,
            code,
            None,
            0,
            output,
            output_size,
            ctypes.byref(returned),
            None,
        )
        if not ok:
            error = ctypes.get_last_error()
            raise OSError(error, ctypes.FormatError(error), self._device_path)
        return output.raw[: returned.value]


def _decode_wchars(raw: bytes) -> str:
    return raw.decode("utf-16-le", errors="replace").split("\x00")[0]


def parse_channel_names(version: int, metadata: bytes) -> List[str]:
    """
    Extract the channel names from an EMI_METADATA_V1/V2 buffer.
    """
    if version == EMI_VERSION_V2:
        # EMI_METADATA_V2: WCHAR[16] OEM, WCHAR[16] Model,
        # USHORT Revision, USHORT ChannelCount, EMI_CHANNEL_V2 Channels[]
        (channel_count,) = struct.unpack_from("<H", metadata, 66)
        names = []
        offset = 68
        for _ in range(channel_count):
            # EMI_CHANNEL_V2: int MeasurementUnit, USHORT ChannelNameSize,
            # WCHAR ChannelName[] (ChannelNameSize is in bytes)
            (name_size,) = struct.unpack_from("<H", metadata, offset + 4)
            raw = metadata[offset + 6 : offset + 6 + name_size]
            names.append(_decode_wchars(raw))
            offset += 6 + name_size
        return names
    if version == EMI_VERSION_V1:
        # EMI_METADATA_V1: int MeasurementUnit, WCHAR[16] OEM, WCHAR[16] Model,
        # USHORT Revision, USHORT MeteredHardwareNameSize, WCHAR MeteredHardwareName[]
        (name_size,) = struct.unpack_from("<H", metadata, 70)
        raw = metadata[72 : 72 + name_size]
        return [_decode_wchars(raw) or "EMI"]
    raise ValueError(f"Unsupported EMI version: {version}")


def parse_measurements(raw: bytes) -> List[Tuple[int, int]]:
    """
    Parse a buffer of EMI_CHANNEL_MEASUREMENT_DATA into a list of
    (absolute_energy_pwh, absolute_time_100ns) tuples.
    """
    measurements = []
    for offset in range(0, len(raw) - EMI_MEASUREMENT_SIZE + 1, EMI_MEASUREMENT_SIZE):
        measurements.append(struct.unpack_from("<QQ", raw, offset))
    return measurements


def _read_device_channels(device_path: str) -> List[str]:
    """Read version + metadata of an EMI device and return its channel names."""
    with _EmiDeviceHandle(device_path) as device:
        (version,) = struct.unpack_from("<H", device.ioctl(IOCTL_EMI_GET_VERSION, 2))
        (metadata_size,) = struct.unpack_from(
            "<L", device.ioctl(IOCTL_EMI_GET_METADATA_SIZE, 4)
        )
        metadata = device.ioctl(IOCTL_EMI_GET_METADATA, metadata_size)
    return parse_channel_names(version, metadata)


def _read_device_measurements(
    device_path: str, channel_count: int
) -> List[Tuple[int, int]]:
    """Read the current measurement of every channel of an EMI device."""
    with _EmiDeviceHandle(device_path) as device:
        raw = device.ioctl(
            IOCTL_EMI_GET_MEASUREMENT, EMI_MEASUREMENT_SIZE * channel_count
        )
    return parse_measurements(raw)


def _is_package_channel(name: str) -> bool:
    return "pkg" in name.lower()


def _is_dram_channel(name: str) -> bool:
    return "dram" in name.lower()


def select_channels(
    device_channels: List[Tuple[str, List[str]]], include_dram: bool = False
) -> Dict[str, List[int]]:
    """
    Select the channels to monitor among all the ones exposed by the machine.

    The selection has to be made globally, over every device at once: Windows
    exposes one EMI device per metered component, so a CPU typically appears as
    one device per core (``RAPL_Package0_Core3_CORE``) alongside the device
    holding the package channel (``RAPL_Package0_PKG``). Package channels
    measure the whole CPU package, while the CORE/PP0/PP1 channels are
    subdomains of that package: measuring both would count the same energy
    twice.

    When no package channel is exposed at all, every channel is kept, as with
    unknown RAPL domains on Linux.

    Returns a mapping of device path to the indices of its selected channels.
    """
    has_package = any(
        _is_package_channel(name) for _, names in device_channels for name in names
    )
    if not has_package:
        logger.warning(
            "\tEMI - No package channel identified among %s, using all channels",
            [name for _, names in device_channels for name in names],
        )
    selection: Dict[str, List[int]] = {}
    for device_path, channel_names in device_channels:
        selected = []
        for index, name in enumerate(channel_names):
            if _is_dram_channel(name):
                keep = include_dram
            elif has_package:
                keep = _is_package_channel(name)
            else:
                keep = True
            if keep:
                selected.append(index)
        if selected:
            selection[device_path] = selected
    return selection


def _counters_match(first: int, second: int) -> bool:
    """Tell whether two counter values are indistinguishable."""
    return abs(first - second) <= MIRRORED_CHANNEL_TOLERANCE * max(first, second)


def find_mirrored_channels(
    channels: List[Tuple[Tuple[str, int], int]],
) -> Dict[Tuple[str, int], Tuple[str, int]]:
    """
    Identify the channels that report the same underlying energy counter.

    ``channels`` is an ordered list of ``(key, absolute_energy_pwh)``.

    Multi-die CPUs (e.g. AMD Ryzen Threadripper / EPYC) expose one package
    channel per die, but every die mirrors the same socket-wide RAPL counter.
    Summing those channels multiplies the reported CPU power by the number of
    dies, exactly like the ``package-0-die-0`` / ``package-0-die-1`` duplicates
    seen through the Linux powercap interface. Two independent meters are
    extremely unlikely to hold the very same picowatt-hour count, so equal
    counters point at duplicated ones.

    Returns a mapping of each duplicating channel to the earlier channel it
    mirrors.
    """
    references: List[Tuple[Tuple[str, int], int]] = []
    mirrored: Dict[Tuple[str, int], Tuple[str, int]] = {}
    for key, energy in channels:
        if energy <= 0:
            continue
        for reference_key, reference in references:
            if _counters_match(energy, reference):
                mirrored[key] = reference_key
                break
        else:
            references.append((key, energy))
    return mirrored


class WindowsEMI:
    """
    A class to interface the Windows Energy Meter Interface (EMI) for
    monitoring CPU power consumption.

    It mirrors the semantics of the Linux `IntelRAPL` interface: EMI exposes
    the same RAPL cumulative energy counters (in picowatt-hours) which are
    read at each measurement and converted to energy deltas.

    Args:
        emi_include_dram (bool): Include DRAM channels in the measurement
                                 (default: False, CPU package only).

    Methods:
        start():
            Takes the initial energy counter snapshot.

        get_cpu_details(duration: Time) -> Dict:
            Fetches the CPU energy deltas since the previous call.

        get_static_cpu_details() -> Dict:
            Returns the last computed CPU details without recalculating them.
    """

    def __init__(self, emi_include_dram: bool = False):
        self._system = sys.platform.lower()
        self.emi_include_dram = emi_include_dram
        # List of (device_path, channel_names, selected_channel_indices)
        self._devices: List[Tuple[str, List[str], List[int]]] = []
        # (device_path, channel_index) -> (absolute_energy_pwh, absolute_time_100ns)
        self._last_measurements: Dict[Tuple[str, int], Tuple[int, int]] = {}
        # Channels that look like a duplicate of another one, but whose energy
        # deltas have not confirmed it yet. They are left out of the
        # measurement while pending.
        self._mirrored_candidates: Dict[Tuple[str, int], Tuple[str, int]] = {}
        self._cpu_details: Dict = {}
        self._setup_emi()

    def _setup_emi(self) -> None:
        if not self._system.startswith("win"):
            raise SystemError("Platform not supported by the Energy Meter Interface")
        device_paths = list_emi_device_paths()
        if not device_paths:
            raise FileNotFoundError(
                "No Energy Meter Interface device found. EMI requires Windows 11 "
                "running on bare metal (or a Windows 10 device with metering hardware)."
            )
        logger.debug("\tEMI - Found %d energy meter device(s)", len(device_paths))
        device_channels: List[Tuple[str, List[str]]] = []
        for device_path in device_paths:
            try:
                channel_names = _read_device_channels(device_path)
            except (OSError, ValueError) as e:
                logger.debug(
                    "\tEMI - Unable to read metadata of %s: %s", device_path, e
                )
                continue
            logger.debug(
                "\tEMI - Device %s exposes the channel(s) %s",
                device_path,
                channel_names,
            )
            device_channels.append((device_path, channel_names))
        selection = select_channels(device_channels, self.emi_include_dram)
        for device_path, channel_names in device_channels:
            selected = selection.get(device_path)
            if not selected:
                continue
            for index in selected:
                logger.debug(
                    "\tEMI - Monitoring channel '%s' of device %s",
                    channel_names[index],
                    device_path,
                )
            self._devices.append((device_path, channel_names, selected))
        if not self._devices:
            raise FileNotFoundError("No readable Energy Meter Interface channel found.")

    def _snapshot(self) -> Dict[Tuple[str, int], Tuple[int, int]]:
        """Read the current counters of all monitored channels."""
        snapshot: Dict[Tuple[str, int], Tuple[int, int]] = {}
        for device_path, channel_names, selected in self._devices:
            try:
                measurements = _read_device_measurements(
                    device_path, len(channel_names)
                )
            except OSError as e:
                logger.info("\tEMI - Unable to read %s: %s", device_path, e)
                continue
            for index in selected:
                if index < len(measurements):
                    snapshot[(device_path, index)] = measurements[index]
        return snapshot

    def _find_mirrored_candidates(
        self, snapshot: Dict[Tuple[str, int], Tuple[int, int]]
    ) -> Dict[Tuple[str, int], Tuple[str, int]]:
        """
        Flag the channels whose counter is indistinguishable from another one's,
        as summing them would over-count the CPU power.
        """
        channels = []
        for device_path, channel_names, selected in self._devices:
            for index in selected:
                # DRAM channels are a different measurement, never a duplicate
                if _is_dram_channel(channel_names[index]):
                    continue
                measurement = snapshot.get((device_path, index))
                if measurement is not None:
                    channels.append(((device_path, index), measurement[0]))
        if len(channels) < 2:
            return {}
        return find_mirrored_channels(channels)

    def _channel_name(self, key: Tuple[str, int]) -> str:
        for device_path, channel_names, _ in self._devices:
            if device_path == key[0]:
                return channel_names[key[1]]
        return str(key)

    def _energy_delta(
        self,
        key: Tuple[str, int],
        snapshot: Dict[Tuple[str, int], Tuple[int, int]],
    ):
        """Energy accumulated by a channel since the previous snapshot."""
        current = snapshot.get(key)
        previous = self._last_measurements.get(key)
        if current is None or previous is None:
            return None
        return current[0] - previous[0]

    def _confirm_mirrored_channels(
        self, snapshot: Dict[Tuple[str, int], Tuple[int, int]]
    ) -> None:
        """
        Decide the fate of the channels flagged as duplicates at ``start()``.

        Two independent meters could hold indistinguishable counters at the
        single instant of the initial snapshot, so a candidate is only dropped
        for good once it has also accumulated the very same energy over a
        measurement interval. A candidate whose energy delta differs is a real
        meter and is restored, and a candidate that has not accumulated
        anything yet stays pending until an interval is conclusive.
        """
        if not self._mirrored_candidates:
            return
        pending: Dict[Tuple[str, int], Tuple[str, int]] = {}
        confirmed: List[Tuple[str, int]] = []
        for key, reference_key in self._mirrored_candidates.items():
            delta = self._energy_delta(key, snapshot)
            reference_delta = self._energy_delta(reference_key, snapshot)
            if delta is None or reference_delta is None:
                pending[key] = reference_key
            elif delta <= 0 and reference_delta <= 0:
                # Nothing was accumulated: the interval is not conclusive
                pending[key] = reference_key
            elif _counters_match(delta, reference_delta):
                confirmed.append(key)
            else:
                logger.info(
                    "\tEMI - Channel '%s' accumulates energy on its own, it is "
                    "an independent meter and is measured again.",
                    self._channel_name(key),
                )
        self._mirrored_candidates = pending
        if confirmed:
            self._drop_channels(confirmed)

    def _drop_channels(self, keys: List[Tuple[str, int]]) -> None:
        """Stop monitoring the given channels."""
        dropped = set(keys)
        devices = []
        for device_path, channel_names, selected in self._devices:
            kept = []
            for index in selected:
                if (device_path, index) in dropped:
                    logger.warning(
                        "\tEMI - Channel '%s' of device %s reports the same energy "
                        "counter as another channel, it is ignored to avoid "
                        "double-counting the CPU power (multi-die CPUs mirror the "
                        "package counter on each die).",
                        channel_names[index],
                        device_path,
                    )
                else:
                    kept.append(index)
            if kept:
                devices.append((device_path, channel_names, kept))
        self._devices = devices

    def start(self) -> None:
        """
        Starts monitoring CPU energy consumption by taking the initial
        counter snapshot.
        """
        snapshot = self._snapshot()
        self._mirrored_candidates = self._find_mirrored_candidates(snapshot)
        self._last_measurements = snapshot

    def get_cpu_details(self, duration: Time) -> Dict:
        """
        Fetches the CPU Energy Deltas by reading the EMI counters and
        subtracting the previous snapshot.
        """
        cpu_details: Dict = {}
        snapshot = self._snapshot()
        self._confirm_mirrored_channels(snapshot)
        channel_index = 0
        for device_path, channel_names, selected in self._devices:
            for index in selected:
                key = (device_path, index)
                if key in self._mirrored_candidates:
                    # Still suspected of duplicating another channel
                    continue
                current = snapshot.get(key)
                previous = self._last_measurements.get(key)
                energy_kwh = 0.0
                power_w = 0.0
                if current and previous:
                    delta_pwh = current[0] - previous[0]
                    delta_time_s = (current[1] - previous[1]) * HNS_TO_S
                    if delta_time_s <= 0:
                        delta_time_s = duration.seconds
                    if delta_pwh >= 0 and delta_time_s > 0:
                        energy_kwh = delta_pwh * PWH_TO_KWH
                        power_w = delta_pwh * PWH_TO_WH * 3600 / delta_time_s
                    else:
                        logger.debug(
                            "\tEMI - Skipping negative delta on channel '%s'",
                            channel_names[index],
                        )
                logger.debug(
                    "\tEMI - Channel '%s' of device %s: %.2f W",
                    channel_names[index],
                    device_path,
                    power_w,
                )
                name = f"Processor Energy Delta_{channel_index}(kWh)"
                cpu_details[name] = energy_kwh
                # We fake the names used by Power Gadget, as IntelRAPL does
                cpu_details[name.replace("Energy", "Power")] = power_w
                channel_index += 1
        self._last_measurements.update(snapshot)
        self._cpu_details = cpu_details
        logger.debug("get_cpu_details %s", self._cpu_details)
        return cpu_details

    def get_static_cpu_details(self) -> Dict:
        """
        Return CPU details without computing them.
        """
        return self._cpu_details


@lru_cache(maxsize=1)
def is_emi_available() -> bool:
    """
    Checks if the Windows Energy Meter Interface is available on the system.

    Returns:
        bool: `True` if EMI is available, `False` otherwise.
    """
    if not _IS_WINDOWS:
        return False
    try:
        emi = WindowsEMI()
        # Make sure the counters are actually readable
        if not emi._snapshot():
            logger.debug("Not using EMI: no readable measurement")
            return False
        return True
    except Exception as e:
        logger.debug(
            "Not using EMI, an exception occurred while instantiating "
            + "WindowsEMI : %s",
            e,
        )
        return False


def clear_emi_cache() -> None:
    is_emi_available.cache_clear()
