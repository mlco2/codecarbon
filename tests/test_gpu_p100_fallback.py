"""
Tests for GPU energy consumption fallback behavior (issue #667).

On Pascal-architecture GPUs (e.g. Tesla P100), pynvml raises
NVMLError_NotSupported for nvmlDeviceGetTotalEnergyConsumption.
These tests verify CodeCarbon gracefully falls back to nvmlDeviceGetPowerUsage
instead of spamming stack traces and reporting 0.0 W.

Key design constraint: the fix makes ZERO extra pynvml calls at init time,
so it is fully compatible with the existing test_gpu_nvidia.py test suite.

Run with:
    pytest tests/test_gpu_p100_fallback.py -vv
"""

import logging
from unittest.mock import MagicMock, patch

import pynvml

from codecarbon.core.gpu_nvidia import NvidiaGPUDevice
from codecarbon.core.units import Energy, Time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_handle():
    return MagicMock(name="nvml_handle")


def _make_nvidia_device(
    energy_side_effect=None,
    energy_return=500_000,
    power_return=150_000,
    name="Tesla P100-PCIE-16GB",
    driver="525.85.12",
):
    """
    Instantiate an NvidiaGPUDevice with pynvml fully mocked.

    The base class __post_init__ calls _get_total_energy_consumption() exactly
    once via _get_energy_kwh(). Our fix adds zero extra calls, so a single
    mock value or side_effect covers init correctly.
    """
    patches = [
        patch("pynvml.nvmlDeviceGetName",
              return_value=name.encode() if isinstance(name, str) else name),
        patch("pynvml.nvmlDeviceGetMemoryInfo",
              return_value=MagicMock(total=16 * 1024**3, used=0, free=16 * 1024**3)),
        patch("pynvml.nvmlDeviceGetUUID", return_value=b"GPU-fake-uuid-0000"),
        patch("pynvml.nvmlDeviceGetEnforcedPowerLimit", return_value=300_000),
        patch("pynvml.nvmlSystemGetDriverVersion",
              return_value=driver.encode() if isinstance(driver, str) else driver),
        patch("pynvml.nvmlDeviceGetPowerUsage", return_value=power_return),
    ]

    if energy_side_effect is not None:
        patches.append(patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                             side_effect=energy_side_effect))
    else:
        patches.append(patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                             return_value=energy_return))

    for p in patches:
        p.start()
    try:
        device = NvidiaGPUDevice(handle=make_mock_handle(), gpu_index=0)
    finally:
        for p in patches:
            p.stop()

    return device


# ---------------------------------------------------------------------------
# Tests: lazy capability detection
# ---------------------------------------------------------------------------


class TestCapabilityDetection:
    """_energy_consumption_supported is detected lazily on first call — no
    extra pynvml calls at init."""

    def test_flag_true_after_successful_init(self):
        """Volta+: flag is True after the single init call succeeds."""
        device = _make_nvidia_device(energy_return=500_000,
                                     name="NVIDIA GeForce RTX 5070 Ti")
        assert device._energy_consumption_supported is True

    def test_flag_false_after_not_supported_at_init(self):
        """P100: NVMLError_NotSupported at init sets flag permanently to False."""
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported())
        assert device._energy_consumption_supported is False

    def test_flag_none_after_transient_error_at_init(self):
        """Generic NVMLError at init leaves flag as None (retry next interval)."""
        device = _make_nvidia_device(
            energy_side_effect=pynvml.NVMLError("System is not in ready state")
        )
        assert device._energy_consumption_supported is None

    def test_uses_power_fallback_true_on_p100(self):
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported())
        assert device.uses_power_fallback is True

    def test_uses_power_fallback_false_on_modern_gpu(self):
        device = _make_nvidia_device(energy_return=500_000,
                                     name="NVIDIA GeForce RTX 5070 Ti")
        assert device.uses_power_fallback is False

    def test_uses_power_fallback_false_when_flag_is_none(self):
        """uses_power_fallback is False when flag is None (not yet confirmed)."""
        device = _make_nvidia_device(
            energy_side_effect=pynvml.NVMLError("System is not in ready state")
        )
        assert device.uses_power_fallback is False


# ---------------------------------------------------------------------------
# Tests: _get_total_energy_consumption return values
# ---------------------------------------------------------------------------


class TestGetTotalEnergyConsumption:

    def test_returns_mj_counter_on_volta_plus(self):
        device = _make_nvidia_device(energy_return=500_000)
        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption", return_value=999_000):
            result = device._get_total_energy_consumption()
        assert result == 999_000

    def test_not_supported_switches_to_fallback_permanently(self):
        """NVMLError_NotSupported permanently activates the power-usage path."""
        device = _make_nvidia_device(energy_return=500_000)
        device._energy_consumption_supported = None  # reset to unprobed

        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=pynvml.NVMLError_NotSupported()), \
             patch("pynvml.nvmlDeviceGetPowerUsage", return_value=200_000), \
             patch("pynvml.nvmlSystemGetDriverVersion", return_value=b"525.85.12"):
            result = device._get_total_energy_consumption()

        assert device._energy_consumption_supported is False
        assert result is not None
        assert isinstance(result, int)

    def test_transient_error_returns_none_flag_stays_none(self):
        """Generic NVMLError returns None and does NOT activate the fallback."""
        device = _make_nvidia_device(energy_return=500_000)
        device._energy_consumption_supported = None

        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=pynvml.NVMLError("System is not in ready state")):
            result = device._get_total_energy_consumption()

        assert result is None
        assert device._energy_consumption_supported is None  # unchanged

    def test_fallback_encodes_power_as_counter_increment(self):
        """Fallback returns last_energy_mJ + power_mW so base-class delta is correct."""
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported())
        device.last_energy = Energy.from_millijoules(1_000_000)  # 1000 J

        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=150_000):
            result = device._get_total_energy_consumption()

        last_mj = device.last_energy.kWh * 3_600_000_000
        assert result == int(last_mj + 150_000)

    def test_fallback_returns_none_when_power_usage_also_fails(self):
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported())
        with patch("pynvml.nvmlDeviceGetPowerUsage",
                   side_effect=pynvml.NVMLError("unknown")):
            result = device._get_total_energy_consumption()
        assert result is None

    def test_transient_error_on_previously_working_gpu_returns_none(self):
        """After working fine, a transient error returns None without disabling fallback."""
        device = _make_nvidia_device(energy_return=500_000)
        assert device._energy_consumption_supported is True

        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=pynvml.NVMLError("transient")):
            result = device._get_total_energy_consumption()

        assert result is None
        assert device._energy_consumption_supported is True  # unchanged


# ---------------------------------------------------------------------------
# Tests: delta() — the core regression check
# ---------------------------------------------------------------------------


class TestDeltaOnP100:
    """The original bug: P100 reported 0.0 W on every interval."""

    def test_power_is_nonzero_on_p100(self):
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported(),
                                     power_return=150_000)
        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=150_000):
            result = device.delta(Time(seconds=15))
        assert result["power_usage"].W > 0, \
            "GPU power was 0 W on a P100-like device — fallback not working"

    def test_energy_delta_is_nonzero_on_p100(self):
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported(),
                                     power_return=200_000)
        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=200_000):
            result = device.delta(Time(seconds=10))
        assert result["delta_energy_consumption"].kWh > 0, \
            "GPU energy was 0 on a P100-like device — fallback not working"

    def test_unchanged_counter_gives_zero_delta_on_volta(self):
        """Sanity: same counter value twice → zero delta."""
        device = _make_nvidia_device(energy_return=500_000)
        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption", return_value=500_000):
            result = device.delta(Time(seconds=10))
        assert result["delta_energy_consumption"].kWh == 0

    def test_transient_error_returns_none_not_fallback(self):
        """Regression: generic NVMLError must NOT activate the P100 fallback."""
        device = _make_nvidia_device(energy_return=500_000)
        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=pynvml.NVMLError("System is not in ready state")):
            result = device._get_total_energy_consumption()
        assert result is None
        assert device._energy_consumption_supported is True


# ---------------------------------------------------------------------------
# Tests: warning logging
# ---------------------------------------------------------------------------


class TestLogging:

    def test_fallback_warning_includes_driver_version(self, caplog):
        # codecarbon sets propagate=False; re-enable for caplog to work.
        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported(),
                                    driver="525.85.12")
        finally:
            cc_logger.propagate = False

        warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("525" in m or "fallback" in m.lower() or "pascal" in m.lower()
                   for m in warnings), \
            f"Expected fallback/driver warning, got: {warnings}"

    def test_no_fallback_warning_on_volta_plus(self, caplog):
        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                _make_nvidia_device(energy_return=500_000,
                                    name="NVIDIA GeForce RTX 5070 Ti")
        finally:
            cc_logger.propagate = False

        fallback_warnings = [r.message for r in caplog.records
                             if r.levelno == logging.WARNING
                             and "fallback" in r.message.lower()]
        assert fallback_warnings == []

    def test_warning_not_repeated_on_subsequent_fallback_calls(self, caplog):
        """Warning fires once at detection, not on every measurement."""
        device = _make_nvidia_device(energy_side_effect=pynvml.NVMLError_NotSupported())

        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=150_000):
                    device._get_total_energy_consumption()
                    device._get_total_energy_consumption()
                    device._get_total_energy_consumption()
        finally:
            cc_logger.propagate = False

        # No new fallback warnings after detection (flag is already False)
        new_fallback_warnings = [r for r in caplog.records
                                 if r.levelno == logging.WARNING
                                 and "fallback" in r.message.lower()]
        assert len(new_fallback_warnings) == 0
