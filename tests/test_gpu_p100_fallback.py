"""
Tests for GPU energy consumption fallback behavior (issue #667).

On Pascal-architecture GPUs (e.g. Tesla P100), pynvml raises
NVMLError_NotSupported for nvmlDeviceGetTotalEnergyConsumption.
These tests verify CodeCarbon gracefully falls back to nvmlDeviceGetPowerUsage
instead of spamming stack traces and reporting 0.0 W.

We extend FakeGPUEnv (from test_gpu_nvidia.py) so that the fake pynvml module
is injected and torn down correctly, exactly as the existing test suite does.

Run with:
    pytest tests/test_gpu_p100_fallback.py -vv
"""

import logging
import os
import sys
from copy import deepcopy
from unittest.mock import patch

# Import FakeGPUEnv from test_gpu_nvidia so we reuse its setup/teardown exactly.
# This ensures the fake pynvml module is injected correctly before each test.
from tests.test_gpu_nvidia import FakeGPUEnv


class TestCapabilityDetection(FakeGPUEnv):
    """_energy_consumption_supported is set lazily on the first call."""

    def test_flag_true_after_successful_init(self):
        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        # Both GPUs succeeded → flag should be True on each
        for device in devices.devices:
            assert device._energy_consumption_supported is True

    def test_flag_false_after_not_supported_at_init(self):
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        for device in devices.devices:
            assert device._energy_consumption_supported is False

    def test_flag_none_after_transient_error_at_init(self):
        import pynvml

        def raise_transient(handle):
            raise pynvml.NVMLError("System is not in ready state")

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_transient
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        for device in devices.devices:
            assert device._energy_consumption_supported is None

    def test_uses_power_fallback_true_on_p100(self):
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        for device in devices.devices:
            assert device.uses_power_fallback is True

    def test_uses_power_fallback_false_on_modern_gpu(self):
        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        for device in devices.devices:
            assert device.uses_power_fallback is False

    def test_uses_power_fallback_false_when_transient_error(self):
        import pynvml

        def raise_transient(handle):
            raise pynvml.NVMLError("System is not in ready state")

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_transient
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        # Transient error → flag is None, not False → uses_power_fallback is False
        for device in devices.devices:
            assert device.uses_power_fallback is False


class TestGetTotalEnergyConsumption(FakeGPUEnv):
    """_get_total_energy_consumption returns the correct value on each path."""

    def test_returns_energy_counter_on_supported_gpu(self):
        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        device = devices.devices[0]

        import pynvml
        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = lambda h: 999_000
            result = device._get_total_energy_consumption()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        assert result == 999_000

    def test_not_supported_switches_to_fallback_permanently(self):
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]
        assert device._energy_consumption_supported is False

        # Next call should use power fallback and return a non-None int
        result = device._get_total_energy_consumption()
        assert result is not None
        assert isinstance(result, int)

    def test_transient_error_returns_none_flag_stays_none(self):
        import pynvml

        def raise_transient(handle):
            raise pynvml.NVMLError("System is not in ready state")

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_transient
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]
        assert device._energy_consumption_supported is None

        # Calling again with transient error still returns None
        pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_transient
        try:
            result = device._get_total_energy_consumption()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        assert result is None
        assert device._energy_consumption_supported is None

    def test_fallback_encodes_power_as_counter_increment(self):
        import pynvml
        from codecarbon.core.units import Energy

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]
        device.last_energy = Energy.from_millijoules(1_000_000)  # 1000 J

        # DETAILS["handle_0"]["power_usage"] = 26_000 mW from FakeGPUEnv
        result = device._get_total_energy_consumption()

        last_mj = device.last_energy.kWh * 3_600_000_000
        expected = int(last_mj + self.DETAILS["handle_0"]["power_usage"])
        assert result == expected

    def test_fallback_returns_none_when_power_usage_also_fails(self):
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        def raise_power_error(handle):
            raise pynvml.NVMLError("power failed")

        original_energy = pynvml.nvmlDeviceGetTotalEnergyConsumption
        original_power = pynvml.nvmlDeviceGetPowerUsage
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
            device = devices.devices[0]
            pynvml.nvmlDeviceGetPowerUsage = raise_power_error
            result = device._get_total_energy_consumption()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original_energy
            pynvml.nvmlDeviceGetPowerUsage = original_power

        assert result is None

    def test_transient_error_on_previously_working_gpu_returns_none(self):
        import pynvml

        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        device = devices.devices[0]
        assert device._energy_consumption_supported is True

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = \
                lambda h: (_ for _ in ()).throw(pynvml.NVMLError("transient"))
            result = device._get_total_energy_consumption()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        assert result is None
        assert device._energy_consumption_supported is True


class TestDeltaOnP100(FakeGPUEnv):
    """delta() must return non-zero power/energy when the fallback is active."""

    def test_power_is_nonzero_on_p100(self):
        """Core regression: P100 must not report 0.0 W."""
        import pynvml
        from codecarbon.core.units import Time

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]
        result = device.delta(Time(seconds=15))
        assert result["power_usage"].W > 0, \
            "GPU power was 0 W on a P100-like device — fallback not working"

    def test_energy_delta_is_nonzero_on_p100(self):
        import pynvml
        from codecarbon.core.units import Time

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]
        result = device.delta(Time(seconds=10))
        assert result["delta_energy_consumption"].kWh > 0, \
            "GPU energy was 0 on a P100-like device — fallback not working"

    def test_unchanged_counter_gives_zero_delta_on_volta(self):
        """Sanity: if counter doesn't change between two delta() calls, delta is zero."""
        import pynvml
        from codecarbon.core.units import Energy, Time

        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        device = devices.devices[0]

        # Seed last_energy to match the fixed counter value so the first
        # delta() call sees no change (counter - last_energy_mJ == 0).
        fixed_value = 500_000
        device.last_energy = Energy.from_millijoules(fixed_value)

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = lambda h: fixed_value
            result = device.delta(Time(seconds=10))
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        assert result["delta_energy_consumption"].kWh == 0

    def test_transient_error_does_not_activate_fallback(self):
        """Generic NVMLError must NOT permanently switch to the power fallback."""
        import pynvml

        from codecarbon.core.gpu import AllGPUDevices
        devices = AllGPUDevices()
        device = devices.devices[0]
        assert device._energy_consumption_supported is True

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = \
                lambda h: (_ for _ in ()).throw(
                    pynvml.NVMLError("System is not in ready state")
                )
            result = device._get_total_energy_consumption()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        assert result is None
        assert device._energy_consumption_supported is True  # unchanged


class TestLogging(FakeGPUEnv):
    """Warning is logged once with driver version when falling back."""

    def test_fallback_warning_includes_driver_version(self, caplog):
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                from codecarbon.core.gpu import AllGPUDevices
                AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original
            cc_logger.propagate = False

        warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("fallback" in m.lower() or "pascal" in m.lower() or "525" in m
                   for m in warnings), \
            f"Expected fallback warning, got: {warnings}"

    def test_no_fallback_warning_on_supported_gpu(self, caplog):
        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                from codecarbon.core.gpu import AllGPUDevices
                AllGPUDevices()
        finally:
            cc_logger.propagate = False

        fallback_warnings = [r.message for r in caplog.records
                             if r.levelno == logging.WARNING
                             and "fallback" in r.message.lower()]
        assert fallback_warnings == []

    def test_warning_not_repeated_on_subsequent_calls(self, caplog):
        """Warning fires once at detection; subsequent fallback calls are silent."""
        import pynvml

        def raise_not_supported(handle):
            raise pynvml.NVMLError_NotSupported()

        original = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_not_supported
            from codecarbon.core.gpu import AllGPUDevices
            devices = AllGPUDevices()
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original

        device = devices.devices[0]

        cc_logger = logging.getLogger("codecarbon")
        cc_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="codecarbon"):
                # Three more calls on the fallback path — no new warnings expected
                device._get_total_energy_consumption()
                device._get_total_energy_consumption()
                device._get_total_energy_consumption()
        finally:
            cc_logger.propagate = False

        new_warnings = [r for r in caplog.records
                        if r.levelno == logging.WARNING
                        and "fallback" in r.message.lower()]
        assert len(new_warnings) == 0
