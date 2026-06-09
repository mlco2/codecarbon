from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from codecarbon.core.resource_tracker import MODE_CPU_LOAD, ResourceTracker


def make_tracker(**overrides):
    tracker = SimpleNamespace(
        _force_ram_power=None,
        _tracking_mode="machine",
        _conf={"cpu_physical_count": 2},
        _hardware=[],
        _output_dir="out",
        _rapl_include_dram=False,
        _rapl_prefer_psys=False,
        _force_cpu_power=None,
        _gpu_ids=None,
    )
    for key, value in overrides.items():
        setattr(tracker, key, value)
    return tracker


@pytest.mark.parametrize(
    "is_mac, is_windows, is_linux, cpu_model, expected_fragment",
    [
        (True, False, False, "Apple M4", "PowerMetrics sudo"),
        (True, False, False, "Intel Core i7", "Intel Power Gadget"),
        (True, False, False, None, "Intel Power Gadget"),
        (False, True, False, "Intel Core i7", "Intel Power Gadget"),
        (False, False, True, "Intel Core i7", "RAPL"),
        (False, False, False, "Intel Core i7", ""),
    ],
)
def test_get_install_instructions(
    is_mac, is_windows, is_linux, cpu_model, expected_fragment
):
    tracker = MagicMock()
    resource_tracker = ResourceTracker(tracker)

    with (
        patch("codecarbon.core.resource_tracker.is_mac_os", return_value=is_mac),
        patch(
            "codecarbon.core.resource_tracker.is_windows_os", return_value=is_windows
        ),
        patch("codecarbon.core.resource_tracker.is_linux_os", return_value=is_linux),
        patch(
            "codecarbon.core.resource_tracker.detect_cpu_model", return_value=cpu_model
        ),
    ):
        result = resource_tracker._get_install_instructions()

    assert expected_fragment in result


def test_set_ram_tracking_uses_forced_power():
    tracker = make_tracker(_force_ram_power=12.5)
    fake_ram = SimpleNamespace(machine_memory_GB=64.0)

    with patch(
        "codecarbon.core.resource_tracker.RAM", return_value=fake_ram
    ) as mock_ram:
        resource_tracker = ResourceTracker(tracker)
        resource_tracker.set_RAM_tracking()

    mock_ram.assert_called_once_with(
        tracking_mode="machine",
        force_ram_power=12.5,
    )
    assert resource_tracker.ram_tracker == "User specified constant: 12.5 Watts"
    assert tracker._conf["ram_total_size"] == 64.0
    assert tracker._hardware == [fake_ram]


def test_setup_cpu_load_mode_returns_false_without_psutil():
    resource_tracker = ResourceTracker(make_tracker())
    tdp = SimpleNamespace(model="Test CPU")

    with patch(
        "codecarbon.core.resource_tracker.cpu.is_psutil_available", return_value=False
    ):
        assert resource_tracker._setup_cpu_load_mode(tdp, 123) is False


def test_setup_cpu_load_mode_updates_tracker_state():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)
    hardware_cpu = MagicMock()
    hardware_cpu.get_model.return_value = "Tracked CPU"
    tdp = SimpleNamespace(model="Test CPU")

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_psutil_available",
            return_value=True,
        ),
        patch(
            "codecarbon.core.resource_tracker.CPU.from_utils", return_value=hardware_cpu
        ) as mock_from_utils,
    ):
        assert resource_tracker._setup_cpu_load_mode(tdp, 123) is True

    mock_from_utils.assert_called_once_with(
        "out",
        MODE_CPU_LOAD,
        "Test CPU",
        123,
        tracking_mode="machine",
    )
    assert resource_tracker.cpu_tracker == MODE_CPU_LOAD
    assert tracker._conf["cpu_model"] == "Tracked CPU"
    assert tracker._hardware == [hardware_cpu]


def test_setup_powermetrics_tracks_cpu_and_gpu():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)
    cpu_chip = MagicMock()
    cpu_chip.get_model.return_value = "Apple CPU"
    gpu_chip = MagicMock()
    gpu_chip.get_model.return_value = "Apple GPU"

    with patch(
        "codecarbon.core.resource_tracker.AppleSiliconChip.from_utils",
        side_effect=[cpu_chip, gpu_chip],
    ) as mock_from_utils:
        assert resource_tracker._setup_powermetrics() is True

    assert mock_from_utils.call_args_list[0].kwargs == {"chip_part": "CPU"}
    assert mock_from_utils.call_args_list[1].kwargs == {"chip_part": "GPU"}
    assert tracker._hardware == [cpu_chip, gpu_chip]
    assert tracker._conf["cpu_model"] == "Apple CPU"
    assert tracker._conf["gpu_model"] == "Apple GPU"
    assert tracker._conf["gpu_count"] == 1


def test_setup_fallback_tracking_uses_cpu_load_when_tdp_matches():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)
    hardware_cpu = MagicMock()
    tdp = SimpleNamespace(model="Matched CPU")

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_psutil_available",
            return_value=True,
        ),
        patch(
            "codecarbon.core.resource_tracker.CPU.from_utils", return_value=hardware_cpu
        ) as mock_from_utils,
        patch.object(
            resource_tracker, "_get_install_instructions", return_value="instructions"
        ),
    ):
        resource_tracker._setup_fallback_tracking(tdp, 150)

    mock_from_utils.assert_called_once_with(
        "out",
        MODE_CPU_LOAD,
        "Matched CPU",
        150,
        tracking_mode="machine",
    )
    assert resource_tracker.cpu_tracker == MODE_CPU_LOAD
    assert tracker._conf["cpu_model"] == "Matched CPU"
    assert tracker._hardware == [hardware_cpu]


def test_setup_fallback_tracking_uses_global_constant_when_no_tdp_and_no_psutil():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)
    hardware_cpu = MagicMock()

    class FalseyTDP:
        model = "Unknown CPU"

        def __bool__(self):
            return False

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_psutil_available",
            return_value=False,
        ),
        patch(
            "codecarbon.core.resource_tracker.CPU.from_utils", return_value=hardware_cpu
        ) as mock_from_utils,
        patch.object(
            resource_tracker, "_get_install_instructions", return_value="instructions"
        ),
    ):
        resource_tracker._setup_fallback_tracking(FalseyTDP(), None)

    mock_from_utils.assert_called_once_with("out", "constant")
    assert resource_tracker.cpu_tracker == "global constant"
    assert tracker._hardware == [hardware_cpu]


def test_set_cpu_tracking_force_mode_uses_cpu_load_and_returns():
    tracker = make_tracker(_conf={"cpu_physical_count": 4, "force_mode_cpu_load": True})
    resource_tracker = ResourceTracker(tracker)
    fake_tdp = SimpleNamespace(tdp=20, model="CPU")

    with (
        patch("codecarbon.core.resource_tracker.cpu.TDP", return_value=fake_tdp),
        patch.object(
            resource_tracker, "_setup_cpu_load_mode", return_value=True
        ) as mock_setup,
    ):
        resource_tracker.set_CPU_tracking()

    mock_setup.assert_called_once_with(fake_tdp, 80)


def test_set_cpu_tracking_prefers_power_gadget():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
            return_value=True,
        ),
        patch(
            "codecarbon.core.resource_tracker.cpu.is_rapl_available", return_value=False
        ),
        patch(
            "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
            return_value=False,
        ),
        patch.object(resource_tracker, "_setup_power_gadget") as mock_power_gadget,
    ):
        resource_tracker.set_CPU_tracking()

    mock_power_gadget.assert_called_once_with()


def test_set_cpu_tracking_prefers_rapl_before_powermetrics():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
            return_value=False,
        ),
        patch(
            "codecarbon.core.resource_tracker.cpu.is_rapl_available", return_value=True
        ),
        patch(
            "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
            return_value=True,
        ),
        patch.object(resource_tracker, "_setup_rapl") as mock_rapl,
    ):
        resource_tracker.set_CPU_tracking()

    mock_rapl.assert_called_once_with()


def test_set_cpu_tracking_falls_back_when_forced_power_is_set():
    tracker = make_tracker(_force_cpu_power=42)
    resource_tracker = ResourceTracker(tracker)
    fake_tdp = SimpleNamespace(tdp=20, model="CPU")

    with (
        patch(
            "codecarbon.core.resource_tracker.cpu.is_powergadget_available",
            return_value=True,
        ),
        patch(
            "codecarbon.core.resource_tracker.cpu.is_rapl_available", return_value=True
        ),
        patch(
            "codecarbon.core.resource_tracker.powermetrics.is_powermetrics_available",
            return_value=True,
        ),
        patch("codecarbon.core.resource_tracker.cpu.TDP", return_value=fake_tdp),
        patch.object(resource_tracker, "_setup_fallback_tracking") as mock_fallback,
    ):
        resource_tracker.set_CPU_tracking()

    mock_fallback.assert_called_once_with(fake_tdp, 42)


def test_set_gpu_tracking_nvidia_populates_conf():
    tracker = make_tracker(_gpu_ids=["0", "1"])
    resource_tracker = ResourceTracker(tracker)
    gpu_devices = MagicMock()
    gpu_devices.devices.get_gpu_static_info.return_value = [
        {"name": "RTX"},
        {"name": "RTX"},
    ]

    with (
        patch(
            "codecarbon.core.resource_tracker.normalize_gpu_ids", return_value=[0, 1]
        ),
        patch(
            "codecarbon.core.resource_tracker.gpu.is_nvidia_system", return_value=True
        ),
        patch(
            "codecarbon.core.resource_tracker.gpu.is_rocm_system", return_value=False
        ),
        patch(
            "codecarbon.core.resource_tracker.GPU.from_utils", return_value=gpu_devices
        ) as mock_from_utils,
    ):
        resource_tracker.set_GPU_tracking()

    mock_from_utils.assert_called_once_with([0, 1])
    assert tracker._conf["gpu_ids"] == [0, 1]
    assert tracker._conf["gpu_count"] == 2
    assert tracker._conf["gpu_model"] == "2 x RTX"
    assert resource_tracker.gpu_tracker == "pynvml"
    assert tracker._hardware == [gpu_devices]


def test_set_gpu_tracking_handles_no_gpu():
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)

    with (
        patch("codecarbon.core.resource_tracker.normalize_gpu_ids", return_value=None),
        patch(
            "codecarbon.core.resource_tracker.gpu.is_nvidia_system", return_value=False
        ),
        patch(
            "codecarbon.core.resource_tracker.gpu.is_rocm_system", return_value=False
        ),
    ):
        resource_tracker.set_GPU_tracking()

    assert tracker._conf["gpu_count"] == 0
    assert tracker._conf["gpu_model"] == ""


def test_set_cpu_gpu_ram_tracking_calls_all_setup_steps():
    resource_tracker = ResourceTracker(make_tracker())

    with (
        patch.object(resource_tracker, "set_RAM_tracking") as mock_ram,
        patch.object(resource_tracker, "set_CPU_tracking") as mock_cpu,
        patch.object(resource_tracker, "set_GPU_tracking") as mock_gpu,
    ):
        resource_tracker.set_CPU_GPU_ram_tracking()

    mock_ram.assert_called_once_with()
    mock_cpu.assert_called_once_with()
    mock_gpu.assert_called_once_with()
