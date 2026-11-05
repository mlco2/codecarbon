from types import SimpleNamespace
from unittest.mock import patch

import pytest

from codecarbon.core import amd_apu
from codecarbon.core.resource_tracker import ResourceTracker
from codecarbon.external.hardware import CPU, MODE_AMD_APU


def make_card(root, name, vendor="0x1002", metrics_format=3, power_uw="70093000"):
    device = root / name / "device"
    hwmon = device / "hwmon" / "hwmon5"
    hwmon.mkdir(parents=True)
    (device / "vendor").write_text(vendor + "\n")
    # metrics_table_header: u16 structure_size, u8 format_revision, u8 content_revision
    (device / "gpu_metrics").write_bytes(bytes([8, 1, metrics_format, 0]))
    if power_uw is not None:
        (hwmon / "power1_input").write_text(power_uw + "\n")
    return hwmon


@pytest.fixture(autouse=True)
def clear_cache():
    amd_apu.clear_apu_cache()
    yield
    amd_apu.clear_apu_cache()


def test_finds_apu_power(tmp_path):
    hwmon = make_card(tmp_path, "card1")
    (tmp_path / "card1-DP-1").mkdir()  # connectors are skipped
    path = amd_apu.find_apu_power_file(str(tmp_path))
    assert path == hwmon / "power1_input"
    assert amd_apu.read_apu_power_watts(path) == pytest.approx(70.093)


def test_discrete_gpu_is_not_an_apu(tmp_path):
    make_card(tmp_path, "card0", metrics_format=1)
    assert amd_apu.find_apu_power_file(str(tmp_path)) is None


def test_non_amd_vendor_is_ignored(tmp_path):
    make_card(tmp_path, "card0", vendor="0x10de")
    assert amd_apu.find_apu_power_file(str(tmp_path)) is None


def test_falls_back_to_average_power(tmp_path):
    hwmon = make_card(tmp_path, "card0", power_uw=None)
    (hwmon / "power1_average").write_text("42000000\n")
    assert amd_apu.find_apu_power_file(str(tmp_path)) == hwmon / "power1_average"


def test_cpu_mode_reads_package_power(tmp_path):
    hwmon = make_card(tmp_path, "card1", power_uw="55000000")
    with patch.object(
        amd_apu, "find_apu_power_file", return_value=hwmon / "power1_input"
    ):
        cpu = CPU.from_utils("out", MODE_AMD_APU, model="AMD RYZEN AI MAX+ 395")
    assert cpu._get_power_from_cpus().W == pytest.approx(55.0)


def make_tracker(**overrides):
    tracker = SimpleNamespace(
        _tracking_mode="machine",
        _conf={"cpu_physical_count": 1},
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


@patch("codecarbon.core.resource_tracker.is_linux_os", return_value=True)
@patch.object(amd_apu, "is_apu_power_available", return_value=True)
def test_apu_replaces_cpu_tracking_and_skips_amd_gpu(_apu, _linux):
    tracker = make_tracker()
    resource_tracker = ResourceTracker(tracker)
    with (
        patch.object(amd_apu, "find_apu_power_file", return_value=None),
        patch(
            "codecarbon.core.resource_tracker.gpu.is_nvidia_system", return_value=False
        ),
        patch("codecarbon.core.resource_tracker.gpu.is_rocm_system", return_value=True),
    ):
        resource_tracker.set_CPU_tracking()
        resource_tracker.set_GPU_tracking()

    assert [type(h) for h in tracker._hardware] == [CPU]
    assert tracker._hardware[0]._mode == MODE_AMD_APU
    assert tracker._conf["gpu_count"] == 0


@patch("codecarbon.core.resource_tracker.is_linux_os", return_value=True)
@patch.object(amd_apu, "is_apu_power_available", return_value=True)
def test_forced_cpu_power_disables_apu_mode(_apu, _linux):
    resource_tracker = ResourceTracker(make_tracker(_force_cpu_power=30))
    assert not resource_tracker._use_amd_apu()


@patch("codecarbon.core.resource_tracker.is_linux_os", return_value=True)
@patch.object(amd_apu, "is_apu_power_available", return_value=True)
def test_nvidia_gpu_keeps_regular_cpu_tracking(_apu, _linux):
    resource_tracker = ResourceTracker(make_tracker())
    with patch(
        "codecarbon.core.resource_tracker.gpu.is_nvidia_system", return_value=True
    ):
        assert not resource_tracker._use_amd_apu()
