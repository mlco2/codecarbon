"""
Tests for GPU energy consumption fallback behavior (issue #667).

On Pascal-architecture GPUs (e.g. Tesla P100), pynvml does not support
nvmlDeviceGetTotalEnergyConsumption. These tests verify that CodeCarbon
gracefully falls back to nvmlDeviceGetPowerUsage (power polling) instead
of spamming stack traces and reporting 0.0 W.

Run with:
    uv run task test-package
or directly:
    pytest tests/test_gpu_p100_fallback.py -vv
"""

from unittest.mock import MagicMock, patch

import pytest
import pynvml

from codecarbon.core.gpu_nvidia import NvidiaGPUDevice
from codecarbon.core.units import Energy


def make_mock_handle():
    """Return a minimal pynvml-handle-like MagicMock."""
    return MagicMock(name="nvml_handle")


def _patch_nvml_base(name="Tesla P100-PCIE-16GB", driver="525.85.12",
                     total_memory=16 * 1024 ** 3):
    """Return a dict of common pynvml patches needed for NvidiaGPUDevice init."""
    return {
        "name": patch("pynvml.nvmlDeviceGetName",
                      return_value=name.encode() if isinstance(name, str) else name),
        "mem":  patch("pynvml.nvmlDeviceGetMemoryInfo",
                      return_value=MagicMock(total=total_memory, used=0,
                                             free=total_memory)),
        "uuid": patch("pynvml.nvmlDeviceGetUUID",
                      return_value=b"GPU-fake-uuid-0000"),
        "plimit": patch("pynvml.nvmlDeviceGetEnforcedPowerLimit",
                        return_value=300_000),
        "driver": patch("pynvml.nvmlSystemGetDriverVersion",
                        return_value=driver.encode()
                        if isinstance(driver, str) else driver),
    }


def _make_nvidia_device(energy_side_effect=None, energy_return=500_000,
                        power_return=150_000, name="Tesla P100-PCIE-16GB"):
    """
    Instantiate an NvidiaGPUDevice with pynvml fully mocked.

    Parameters
    ----------
    energy_side_effect:
        If set, nvmlDeviceGetTotalEnergyConsumption raises this at every call.
        Pass ``pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)`` to simulate
        a Pascal GPU (P100).
    energy_return:
        Return value for nvmlDeviceGetTotalEnergyConsumption (mJ counter).
    power_return:
        Return value for nvmlDeviceGetPowerUsage (milliwatts).
    """
    base = _patch_nvml_base(name=name)

    if energy_side_effect is not None:
        energy_patch = patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                             side_effect=energy_side_effect)
    else:
        energy_patch = patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                             return_value=energy_return)

    power_patch = patch("pynvml.nvmlDeviceGetPowerUsage",
                        return_value=power_return)

    all_patches = list(base.values()) + [energy_patch, power_patch]
    for p in all_patches:
        p.start()

    device = NvidiaGPUDevice(handle=make_mock_handle(), gpu_index=0)

    for p in all_patches:
        p.stop()

    return device


class TestNvidiaGPUDeviceCapabilityProbe:
    """NvidiaGPUDevice correctly detects energy-counter support at init."""

    def test_volta_plus_marks_energy_supported(self):
        device = _make_nvidia_device(energy_side_effect=None,
                                     name="NVIDIA GeForce RTX 5070 Ti")
        assert device._energy_consumption_supported is True

    def test_pascal_p100_marks_energy_not_supported(self):
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error)
        assert device._energy_consumption_supported is False

    def test_uses_power_fallback_property_true_on_p100(self):
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error)
        assert device.uses_power_fallback is True

    def test_uses_power_fallback_property_false_on_modern_gpu(self):
        device = _make_nvidia_device(energy_side_effect=None,
                                     name="NVIDIA GeForce RTX 5070 Ti")
        assert device.uses_power_fallback is False


class TestGetTotalEnergyConsumption:
    """_get_total_energy_consumption returns the correct value for each path."""

    def test_returns_mj_counter_on_supported_gpu(self):
        device = _make_nvidia_device(energy_side_effect=None, energy_return=999_000)

        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   return_value=999_000):
            result = device._get_total_energy_consumption()

        assert result == 999_000

    def test_fallback_uses_power_usage_on_p100(self):
        """On P100, _get_total_energy_consumption returns a value derived from
        nvmlDeviceGetPowerUsage rather than None."""
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error, power_return=200_000)

        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=200_000):
            result = device._get_total_energy_consumption()

        # Must be a non-None numeric value (the exact value depends on last_energy)
        assert result is not None
        assert isinstance(result, int)

    def test_fallback_result_encodes_power_reading(self):
        """The fallback value equals last_energy_mJ + power_mW (1 s increment)."""
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error, power_return=150_000)

        # Manually set last_energy to a known value
        device.last_energy = Energy.from_millijoules(1_000_000)  # 1000 J

        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=150_000):
            result = device._get_total_energy_consumption()

        last_mj = device.last_energy.kWh * 3_600_000_000
        expected = int(last_mj + 150_000)
        assert result == expected

    def test_fallback_returns_none_when_power_usage_fails(self):
        """If nvmlDeviceGetPowerUsage also fails, returns None without raising."""
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error)

        with patch("pynvml.nvmlDeviceGetPowerUsage",
                   side_effect=pynvml.NVMLError(pynvml.NVML_ERROR_UNKNOWN)):
            result = device._get_total_energy_consumption()

        assert result is None

    def test_supported_gpu_returns_none_on_unexpected_error(self):
        """Unexpected NVMLError on a supported GPU -> returns None, no crash."""
        device = _make_nvidia_device(energy_side_effect=None)

        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=pynvml.NVMLError(pynvml.NVML_ERROR_UNKNOWN)):
            result = device._get_total_energy_consumption()

        assert result is None


class TestDeltaOnP100:
    """delta() must return non-zero power when the fallback path is active."""

    def test_delta_power_nonzero_on_p100(self):
        """The core regression: P100 should not report 0.0 W."""
        from codecarbon.core.units import Time

        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error, power_return=150_000)

        measurement_interval = Time(seconds=15)

        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=150_000):
            result = device.delta(measurement_interval)

        # Power should be close to 150 W (150_000 mW), not 0
        assert result["power_usage"].W > 0, (
            "GPU power was 0 W on a P100-like device - fallback not working"
        )

    def test_delta_energy_nonzero_on_p100(self):
        from codecarbon.core.units import Time

        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)
        device = _make_nvidia_device(energy_side_effect=error, power_return=200_000)

        measurement_interval = Time(seconds=10)

        with patch("pynvml.nvmlDeviceGetPowerUsage", return_value=200_000):
            result = device.delta(measurement_interval)

        assert result["delta_energy_consumption"].kWh > 0, (
            "GPU energy delta was 0 on a P100-like device - fallback not working"
        )

    def test_delta_is_zero_on_supported_gpu_with_unchanged_counter(self):
        """Sanity check: if the energy counter doesn't move, delta is 0."""
        from codecarbon.core.units import Time

        device = _make_nvidia_device(energy_side_effect=None, energy_return=500_000)

        measurement_interval = Time(seconds=10)

        # Same value both times -> no energy consumed
        with patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   return_value=500_000):
            result = device.delta(measurement_interval)

        assert result["delta_energy_consumption"].kWh == 0


class TestDriverVersionLogging:
    """When falling back, the warning message includes the driver version."""

    def test_warning_includes_driver_version(self, caplog):
        import logging

        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)

        # codecarbon sets logger.propagate = False, so caplog won't capture
        # messages unless we temporarily re-enable propagation.
        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                _make_nvidia_device(energy_side_effect=error)
        finally:
            cc_logger.propagate = False

        warnings = [r.message for r in caplog.records
                    if r.levelno == logging.WARNING]
        assert any("525" in m or "fallback" in m.lower() or "pascal" in m.lower()
                   for m in warnings), (
            f"Expected fallback/driver warning, got: {warnings}"
        )

    def test_no_fallback_warning_on_supported_gpu(self, caplog):
        import logging

        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                _make_nvidia_device(energy_side_effect=None,
                                    name="NVIDIA GeForce RTX 5070 Ti")
        finally:
            cc_logger.propagate = False

        fallback_warnings = [r.message for r in caplog.records
                             if r.levelno == logging.WARNING
                             and "fallback" in r.message.lower()]
        assert fallback_warnings == []


class TestAllGPUDevicesWithP100:
    """AllGPUDevices initialises correctly when one GPU lacks energy-counter support."""

    def test_initialises_without_crash_on_p100(self):
        error = pynvml.NVMLError(pynvml.NVML_ERROR_NOT_SUPPORTED)

        with patch("pynvml.nvmlInit"), \
             patch("pynvml.nvmlDeviceGetCount", return_value=1), \
             patch("pynvml.nvmlDeviceGetHandleByIndex",
                   return_value=make_mock_handle()), \
             patch("pynvml.nvmlDeviceGetName",
                   return_value=b"Tesla P100-PCIE-16GB"), \
             patch("pynvml.nvmlDeviceGetMemoryInfo",
                   return_value=MagicMock(total=16 * 1024 ** 3, used=0,
                                         free=16 * 1024 ** 3)), \
             patch("pynvml.nvmlDeviceGetUUID",
                   return_value=b"GPU-fake-uuid-p100"), \
             patch("pynvml.nvmlDeviceGetEnforcedPowerLimit",
                   return_value=300_000), \
             patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   side_effect=error), \
             patch("pynvml.nvmlDeviceGetPowerUsage", return_value=100_000), \
             patch("pynvml.nvmlSystemGetDriverVersion",
                   return_value=b"525.85.12"), \
             patch("codecarbon.core.gpu_nvidia.PYNVML_AVAILABLE", True):

            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()

        assert len(devices.devices) == 1
        assert devices.devices[0].uses_power_fallback is True

    def test_no_fallback_on_modern_gpu(self):
        with patch("pynvml.nvmlInit"), \
             patch("pynvml.nvmlDeviceGetCount", return_value=1), \
             patch("pynvml.nvmlDeviceGetHandleByIndex",
                   return_value=make_mock_handle()), \
             patch("pynvml.nvmlDeviceGetName",
                   return_value=b"NVIDIA GeForce RTX 5070 Ti"), \
             patch("pynvml.nvmlDeviceGetMemoryInfo",
                   return_value=MagicMock(total=12 * 1024 ** 3, used=0,
                                         free=12 * 1024 ** 3)), \
             patch("pynvml.nvmlDeviceGetUUID",
                   return_value=b"GPU-fake-uuid-rtx"), \
             patch("pynvml.nvmlDeviceGetEnforcedPowerLimit",
                   return_value=285_000), \
             patch("pynvml.nvmlDeviceGetTotalEnergyConsumption",
                   return_value=500_000), \
             patch("pynvml.nvmlSystemGetDriverVersion",
                   return_value=b"560.28.03"), \
             patch("codecarbon.core.gpu_nvidia.PYNVML_AVAILABLE", True):

            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()

        assert len(devices.devices) == 1
        assert devices.devices[0].uses_power_fallback is False
