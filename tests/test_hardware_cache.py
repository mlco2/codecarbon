from types import SimpleNamespace
from unittest.mock import patch

import pytest

from codecarbon.core import hardware_cache
from codecarbon.core.cpu import clear_powergadget_cache, is_powergadget_available
from codecarbon.core.powermetrics import clear_powermetrics_cache
from codecarbon.external.hardware import CPU
from codecarbon.external.ram import RAM


def make_tracker(**overrides):
    defaults = {
        "_tracking_mode": "machine",
        "_force_cpu_power": None,
        "_force_ram_power": None,
        "_conf": {},
        "_gpu_ids": None,
        "_rapl_include_dram": False,
        "_rapl_prefer_psys": False,
        "_output_dir": "out",
        "_hardware": [],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_make_key_normalizes_gpu_ids():
    tracker = make_tracker(_gpu_ids=[0, 1])
    key = hardware_cache.make_key(tracker)
    assert key.gpu_ids == (0, 1)


def test_spec_and_rebuild_roundtrip_for_cpu():
    cpu_hw = CPU.from_utils("out", "cpu_load", "Test CPU", 100)
    spec = hardware_cache._spec_from_hardware(cpu_hw)
    rebuilt = hardware_cache._hardware_from_spec(spec, "out2")
    assert type(rebuilt).__name__ == "CPU"
    assert rebuilt._model == "Test CPU"
    assert rebuilt._mode == "cpu_load"


def test_spec_from_hardware_gpu_and_rapl_cpu():
    gpu_hw = type("GPU", (), {"gpu_ids": [0, 1]})()
    assert hardware_cache._spec_from_hardware(gpu_hw) == {
        "kind": "gpu",
        "gpu_ids": [0, 1],
    }

    cpu_hw = type(
        "CPU",
        (),
        {
            "_mode": "intel_rapl",
            "_model": "Intel CPU",
            "_tdp": 65,
            "_tracking_mode": "machine",
            "_intel_interface": SimpleNamespace(
                rapl_include_dram=True,
                rapl_prefer_psys=True,
            ),
        },
    )()
    spec = hardware_cache._spec_from_hardware(cpu_hw)
    assert spec["rapl_include_dram"] is True
    assert spec["rapl_prefer_psys"] is True


def test_spec_and_rebuild_roundtrip_for_apple_chip():
    spec = {"kind": "apple_chip", "model": "Apple M1", "chip_part": "CPU"}
    fake_chip = SimpleNamespace(_model="Apple M1")
    with patch(
        "codecarbon.external.hardware.AppleSiliconChip",
        return_value=fake_chip,
    ) as mock_chip_cls:
        rebuilt = hardware_cache._hardware_from_spec(spec, "out")
    mock_chip_cls.assert_called_once_with(
        output_dir="out",
        model="Apple M1",
        chip_part="CPU",
    )
    assert rebuilt._model == "Apple M1"


def test_capture_and_apply_restore_hardware_plan():
    tracker = make_tracker(
        _conf={"cpu_model": "Cached CPU", "gpu_count": 0, "gpu_model": ""},
        _hardware=[RAM(tracking_mode="machine")],
    )
    resource_tracker = SimpleNamespace(
        tracker=tracker,
        ram_tracker="cached_ram",
        cpu_tracker="cached_cpu",
        gpu_tracker="cached_gpu",
    )
    plan = hardware_cache.capture(resource_tracker)

    tracker2 = make_tracker()
    rt2 = SimpleNamespace(
        tracker=tracker2,
        ram_tracker="old",
        cpu_tracker="old",
        gpu_tracker="old",
    )
    hardware_cache.apply(rt2, plan)

    assert rt2.ram_tracker == "cached_ram"
    assert rt2.cpu_tracker == "cached_cpu"
    assert tracker2._conf["cpu_model"] == "Cached CPU"
    assert len(tracker2._hardware) == 1
    assert type(tracker2._hardware[0]).__name__ == "RAM"


def test_get_or_run_setup_runs_setup_once():
    tracker = make_tracker()
    resource_tracker = SimpleNamespace(
        tracker=tracker,
        ram_tracker="Unspecified",
        cpu_tracker="Unspecified",
        gpu_tracker="Unspecified",
    )
    calls = {"count": 0}

    def setup_fn():
        calls["count"] += 1
        resource_tracker.ram_tracker = "ran"

    hardware_cache.clear_cache()
    hardware_cache.get_or_run_setup(resource_tracker, setup_fn)
    hardware_cache.get_or_run_setup(resource_tracker, setup_fn)

    assert calls["count"] == 1
    assert resource_tracker.ram_tracker == "ran"


def test_hardware_kind_rejects_unknown_type():
    with pytest.raises(TypeError):
        hardware_cache._hardware_kind(object())


def test_clear_cache_resets_probe_caches():
    from codecarbon.core import cpu, powermetrics

    with patch("codecarbon.core.cpu.IntelPowerGadget", side_effect=Exception("nope")):
        is_powergadget_available()
    cpu._powergadget_available = False
    powermetrics._powermetrics_available = False

    hardware_cache.clear_cache()

    assert cpu._powergadget_available is None
    assert powermetrics._powermetrics_available is None


def test_get_cached_tdp_reuses_instance():
    hardware_cache.clear_cache()
    fake_cpu = SimpleNamespace(TDP=lambda: SimpleNamespace(model="cached"))
    first = hardware_cache.get_cached_tdp(fake_cpu)
    second = hardware_cache.get_cached_tdp(fake_cpu)
    assert first is second


def test_clear_powergadget_and_powermetrics_helpers():
    from codecarbon.core import cpu, powermetrics

    cpu._powergadget_available = False
    powermetrics._powermetrics_available = False
    clear_powergadget_cache()
    clear_powermetrics_cache()
    assert cpu._powergadget_available is None
    assert powermetrics._powermetrics_available is None
