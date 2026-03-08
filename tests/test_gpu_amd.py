# -*- coding: utf-8 -*-

# Copyright (C) 2020 [COMET-ML]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from types import SimpleNamespace
from unittest import mock

import pytest


class TestAmdGpu:
    def test_reinit_on_amdsmi_not_initialized_error(self):
        from codecarbon.core.gpu import AMDGPUDevice

        class FakeAmdSmiLibraryException(Exception):
            def __init__(self, ret_code):
                self.ret_code = ret_code
                super().__init__(
                    f"Error code:\n        {ret_code} | AMDSMI_STATUS_NOT_INIT - Device not initialized"
                )

        call_counter = {"count": 0}

        def flaky_vram_usage(_handle):
            if call_counter["count"] == 0:
                call_counter["count"] += 1
                raise FakeAmdSmiLibraryException(32)
            return {"vram_total": 1000, "vram_used": 250}

        fake_amdsmi = SimpleNamespace(
            amdsmi_exception=SimpleNamespace(
                AmdSmiLibraryException=FakeAmdSmiLibraryException
            ),
            amdsmi_init=mock.MagicMock(),
            amdsmi_get_gpu_vram_usage=mock.MagicMock(side_effect=flaky_vram_usage),
        )

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            memory = device._get_memory_info()

        assert fake_amdsmi.amdsmi_init.call_count == 1
        assert fake_amdsmi.amdsmi_get_gpu_vram_usage.call_count == 2
        assert memory.total == 1000 * 1024 * 1024
        assert memory.used == 250 * 1024 * 1024
        assert memory.free == 750 * 1024 * 1024

    def test_no_reinit_on_other_amdsmi_library_error(self):
        from codecarbon.core.gpu import AMDGPUDevice

        class FakeAmdSmiLibraryException(Exception):
            def __init__(self, ret_code):
                self.ret_code = ret_code
                super().__init__(
                    f"Error code:\n        {ret_code} | SOME_OTHER_AMDSMI_ERROR"
                )

        fake_amdsmi = SimpleNamespace(
            amdsmi_exception=SimpleNamespace(
                AmdSmiLibraryException=FakeAmdSmiLibraryException
            ),
            amdsmi_init=mock.MagicMock(),
            amdsmi_get_gpu_vram_usage=mock.MagicMock(
                side_effect=FakeAmdSmiLibraryException(31)
            ),
        )

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            with pytest.raises(FakeAmdSmiLibraryException):
                device._get_memory_info()

        assert fake_amdsmi.amdsmi_init.call_count == 0
        assert fake_amdsmi.amdsmi_get_gpu_vram_usage.call_count == 1

    def test_warn_dual_gcd_models_generic_once_device_specific_each_selection(self):
        from codecarbon.core.gpu import AMDGPUDevice

        AMDGPUDevice._dual_gcd_warning_emitted = False

        device_1 = AMDGPUDevice.__new__(AMDGPUDevice)
        device_1.gpu_index = 0
        device_1._get_gpu_name = mock.MagicMock(return_value="AMD Instinct MI300X")
        device_1._get_uuid = mock.MagicMock(return_value="uuid-1")
        device_1._get_power_limit = mock.MagicMock(return_value=700)
        device_1._get_memory_info = mock.MagicMock(
            return_value=SimpleNamespace(total=1024)
        )

        device_2 = AMDGPUDevice.__new__(AMDGPUDevice)
        device_2.gpu_index = 1
        device_2._get_gpu_name = mock.MagicMock(return_value="AMD Instinct MI300X")
        device_2._get_uuid = mock.MagicMock(return_value="uuid-2")
        device_2._get_power_limit = mock.MagicMock(return_value=700)
        device_2._get_memory_info = mock.MagicMock(
            return_value=SimpleNamespace(total=1024)
        )

        with mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock:
            device_1._init_static_details()
            device_2._init_static_details()
            device_1.emit_selection_warning()
            device_2.emit_selection_warning()

        assert device_1._known_zero_energy_counter is True
        assert device_2._known_zero_energy_counter is True
        # Generic warning is emitted once, then one device-specific warning per selected device
        assert warning_mock.call_count == 3

        AMDGPUDevice._dual_gcd_warning_emitted = False

    def test_get_total_energy_consumption_returns_zero_for_known_dual_gcd_model(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_energy_count=mock.MagicMock())

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._known_zero_energy_counter = True
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"energy_accumulator": 0, "counter_resolution": 1000}
        )
        device._get_gpu_metrics_info = mock.MagicMock(
            return_value={"energy_accumulator": 0}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            result = device._get_total_energy_consumption()

        assert result == 0

    def test_get_total_energy_consumption_returns_none_for_other_models(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_energy_count=mock.MagicMock())

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._known_zero_energy_counter = False
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"energy_accumulator": 0, "counter_resolution": 1000}
        )
        device._get_gpu_metrics_info = mock.MagicMock(
            return_value={"energy_accumulator": 0}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            result = device._get_total_energy_consumption()

        assert result is None

    def test_is_dual_gcd_power_limited_model_mi210(self):
        from codecarbon.core.gpu import AMDGPUDevice

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        assert device._is_dual_gcd_power_limited_model("AMD Instinct MI210") is False

    def test_emit_selection_warning_noop_when_not_dual_gcd(self):
        from codecarbon.core.gpu import AMDGPUDevice

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device._known_zero_energy_counter = False
        device.gpu_index = 0
        device._gpu_name = "AMD Instinct MI100"

        with mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock:
            device.emit_selection_warning()

        warning_mock.assert_not_called()

    def test_get_gpu_metrics_info_calls_amdsmi(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_gpu_metrics_info=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(return_value={"ok": True})

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            result = device._get_gpu_metrics_info()

        device._call_amdsmi_with_reinit.assert_called_once_with(
            fake_amdsmi.amdsmi_get_gpu_metrics_info, "fake_handle"
        )
        assert result == {"ok": True}

    def test_get_total_energy_consumption_uses_power_key(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_energy_count=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"power": 123, "counter_resolution": 1000}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            result = device._get_total_energy_consumption()

        assert result == 123

    def test_get_total_energy_consumption_missing_keys_warns(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_energy_count=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"counter_resolution": 1000}
        )

        with (
            mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True),
            mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock,
        ):
            result = device._get_total_energy_consumption()

        assert result is None
        warning_mock.assert_called()

    def test_get_total_energy_consumption_exception_warns(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_energy_count=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(side_effect=Exception("boom"))

        with (
            mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True),
            mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock,
        ):
            result = device._get_total_energy_consumption()

        assert result is None
        warning_mock.assert_called()

    def test_get_gpu_name_success_and_failure(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_gpu_asic_info=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"market_name": "AMD Instinct MI100"}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_gpu_name() == "AMD Instinct MI100"

        device._call_amdsmi_with_reinit = mock.MagicMock(side_effect=Exception("boom"))
        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_gpu_name() == "Unknown GPU"

    def test_get_uuid(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_gpu_device_uuid=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(return_value="uuid-123")

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_uuid() == "uuid-123"

    def test_get_temperature_fallback_and_exception(self):
        from codecarbon.core.gpu import AMDGPUDevice

        class FakeAmdSmiLibraryException(Exception):
            pass

        fake_amdsmi = SimpleNamespace(
            amdsmi_exception=SimpleNamespace(
                AmdSmiLibraryException=FakeAmdSmiLibraryException
            ),
            AmdSmiTemperatureType=SimpleNamespace(HOTSPOT="hotspot"),
            AmdSmiTemperatureMetric=SimpleNamespace(CURRENT="current"),
            amdsmi_get_temp_metric=mock.MagicMock(),
        )

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(return_value=0)
        device._get_gpu_metrics_info = mock.MagicMock(
            return_value={"temperature_hotspot": 42}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_temperature() == 42

        device._call_amdsmi_with_reinit = mock.MagicMock(
            side_effect=FakeAmdSmiLibraryException("fail")
        )
        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_temperature() == 0

    def test_get_power_usage_fallback_paths(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_power_info=mock.MagicMock())

        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"average_socket_power": "bad"}
        )
        device._get_gpu_metrics_info = mock.MagicMock(
            return_value={"average_socket_power": 75}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_power_usage() == 75

        device._get_gpu_metrics_info = mock.MagicMock(
            return_value={"average_socket_power": "bad"}
        )
        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_power_usage() == 0

    def test_get_power_limit_success_and_exception(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_power_cap_info=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"power_cap": 2_000_000}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_power_limit() == 2

        device._call_amdsmi_with_reinit = mock.MagicMock(side_effect=Exception("boom"))
        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_power_limit() is None

    def test_get_gpu_utilization_and_compute_mode(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_gpu_activity=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value={"gfx_activity": 87}
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_gpu_utilization() == 87
            assert device._get_compute_mode() is None

    def test_get_compute_and_graphics_processes(self):
        from codecarbon.core.gpu import AMDGPUDevice

        fake_amdsmi = SimpleNamespace(amdsmi_get_gpu_process_list=mock.MagicMock())
        device = AMDGPUDevice.__new__(AMDGPUDevice)
        device.handle = "fake_handle"
        device._call_amdsmi_with_reinit = mock.MagicMock(
            return_value=[
                {"pid": 1, "mem": 10, "engine_usage": {"gfx": 0}},
                {"pid": 2, "mem": 20, "engine_usage": {"gfx": 5}},
            ]
        )

        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_compute_processes() == [
                {"pid": 1, "used_memory": 10},
                {"pid": 2, "used_memory": 20},
            ]
            assert device._get_graphics_processes() == [{"pid": 2, "used_memory": 20}]

        device._call_amdsmi_with_reinit = mock.MagicMock(side_effect=Exception("boom"))
        with mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True):
            assert device._get_compute_processes() == []
            assert device._get_graphics_processes() == []


class TestAllGPUDevicesAmd:
    def test_init_with_no_amd_handles(self):
        from codecarbon.core.gpu import AllGPUDevices

        fake_amdsmi = SimpleNamespace(
            amdsmi_init=mock.MagicMock(),
            amdsmi_get_processor_handles=mock.MagicMock(return_value=[]),
            amdsmi_get_gpu_device_uuid=mock.MagicMock(return_value="uuid"),
        )

        with (
            mock.patch("codecarbon.core.gpu.AMDSMI_AVAILABLE", True),
            mock.patch("codecarbon.core.gpu.PYNVML_AVAILABLE", False),
            mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True),
            mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock,
        ):
            AllGPUDevices()

        warning_mock.assert_called_once_with(
            "No AMD GPUs found on machine with amdsmi_get_processor_handles() !"
        )

    def test_init_with_amd_handles_and_bdf_fallback(self):
        from codecarbon.core.gpu import AllGPUDevices

        class DummyAmdDevice:
            def __init__(self, handle, gpu_index):
                self.handle = handle
                self.gpu_index = gpu_index

        fake_amdsmi = SimpleNamespace(
            amdsmi_init=mock.MagicMock(),
            amdsmi_get_processor_handles=mock.MagicMock(return_value=["h1", "h2"]),
            amdsmi_get_gpu_device_bdf=mock.MagicMock(
                side_effect=["0000:01:00.0", Exception("boom")]
            ),
            amdsmi_get_gpu_device_uuid=mock.MagicMock(
                side_effect=lambda handle: f"uuid-{handle}"
            ),
        )

        with (
            mock.patch("codecarbon.core.gpu.AMDSMI_AVAILABLE", True),
            mock.patch("codecarbon.core.gpu.PYNVML_AVAILABLE", False),
            mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True),
            mock.patch("codecarbon.core.gpu.AMDGPUDevice", DummyAmdDevice),
        ):
            devices = AllGPUDevices()

        assert [d.handle for d in devices.devices] == ["h1", "h2"]

    def test_init_amd_exception_warns(self):
        from codecarbon.core.gpu import AllGPUDevices

        class FakeAmdSmiException(Exception):
            pass

        fake_amdsmi = SimpleNamespace(
            amdsmi_init=mock.MagicMock(side_effect=FakeAmdSmiException("boom")),
            AmdSmiException=FakeAmdSmiException,
        )

        with (
            mock.patch("codecarbon.core.gpu.AMDSMI_AVAILABLE", True),
            mock.patch("codecarbon.core.gpu.PYNVML_AVAILABLE", False),
            mock.patch("codecarbon.core.gpu_amd.amdsmi", fake_amdsmi, create=True),
            mock.patch("codecarbon.core.gpu.logger.warning") as warning_mock,
        ):
            AllGPUDevices()

        warning_mock.assert_called()

    def test_methods_handle_exceptions_and_start(self):
        from codecarbon.core.gpu import AllGPUDevices
        from codecarbon.core.units import Time

        class ExplodingDevice:
            def __init__(self):
                self.started = False

            def start(self):
                self.started = True

            def get_static_details(self):
                raise RuntimeError("boom")

            def get_gpu_details(self):
                raise RuntimeError("boom")

            def delta(self, _duration):
                raise RuntimeError("boom")

        devices = AllGPUDevices.__new__(AllGPUDevices)
        exploding = ExplodingDevice()
        devices.devices = [exploding]
        devices.device_count = 1

        devices.start()
        assert exploding.started is True
        assert devices.get_gpu_static_info() == []
        assert devices.get_gpu_details() == []
        assert devices.get_delta(Time(1)) == []
