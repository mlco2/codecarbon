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

import builtins
import importlib.util
import os.path
import sys
from copy import copy, deepcopy
from types import ModuleType, SimpleNamespace
from unittest import TestCase, mock

import pynvml as real_pynvml
import pytest

tc = TestCase()


class FakeGPUEnv:
    def setup_method(self):
        self.old_sys_path = copy(sys.path)
        fake_module_path = os.path.join(os.path.dirname(__file__), "fake_modules")
        sys.path.insert(0, fake_module_path)

        # Clean old modules
        try:
            del sys.modules["pynvml"]
        except KeyError:
            pass

        try:
            del sys.modules["codecarbon.core.gpu"]
        except KeyError:
            pass
        for module_name in (
            "codecarbon.core.gpu_amd",
            "codecarbon.core.gpu_nvidia",
            "codecarbon.core.gpu_device",
        ):
            sys.modules.pop(module_name, None)

        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)

        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)

        # Setup the state, strings are returned as bytes
        self.DETAILS = {
            "handle_0": {
                "name": b"GeForce GTX 1080",
                "uuid": b"uuid-1",
                "memory": real_pynvml.c_nvmlMemory_t(1024, 100, 924),
                "temperature": 75,
                "power_usage": 26000,
                "total_energy_consumption": 1000,
                "power_limit": 149000,
                "utilization_rate": real_pynvml.c_nvmlUtilization_t(96, 0),
                "compute_mode": 0,
                "compute_processes": [
                    real_pynvml.c_nvmlProcessInfo_t(16, 1024 * 1024),
                    real_pynvml.c_nvmlProcessInfo_t(32, 2 * 1024 * 1024),
                ],
                "graphics_processes": [],
            },
            "handle_1": {
                "name": b"GeForce GTX 1080",
                "uuid": b"uuid-2",
                "memory": real_pynvml.c_nvmlMemory_t(1024, 200, 824),
                "temperature": 79,
                "power_usage": 29000,
                "total_energy_consumption": 800,
                "power_limit": 149000,
                "utilization_rate": real_pynvml.c_nvmlUtilization_t(0, 100),
                "compute_mode": 2,
                "compute_processes": [],
                "graphics_processes": [
                    real_pynvml.c_nvmlProcessInfo_t(8, 1024 * 1024 * 1024),
                    real_pynvml.c_nvmlProcessInfo_t(64, 2 * 1024 * 1024 * 1024),
                ],
            },
        }
        self.expected = [
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid-1",
                "gpu_index": 0,
                "total_memory": 1024,
                "free_memory": 100,
                "used_memory": 924,
                "temperature": 75,
                "power_usage": 26,
                "power_limit": 149,
                "total_energy_consumption": 1000,
                "gpu_utilization": 96,
                "compute_mode": 0,
                "compute_processes": [
                    {"pid": 16, "used_memory": 1024 * 1024},
                    {"pid": 32, "used_memory": 2 * 1024 * 1024},
                ],
                "graphics_processes": [],
            },
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid-2",
                "gpu_index": 1,
                "total_memory": 1024,
                "free_memory": 200,
                "used_memory": 824,
                "temperature": 79,
                "power_usage": 29,
                "power_limit": 149,
                "total_energy_consumption": 800,
                "gpu_utilization": 0,
                "compute_mode": 2,
                "compute_processes": [],
                "graphics_processes": [
                    {"pid": 8, "used_memory": 1024 * 1024 * 1024},
                    {"pid": 64, "used_memory": 2 * 1024 * 1024 * 1024},
                ],
            },
        ]
        import pynvml

        pynvml.DETAILS = self.DETAILS
        pynvml.INIT_MOCK.reset_mock()

    def teardown_method(self):
        # Restore the old paths
        sys.path = self.old_sys_path
        try:
            del sys.modules["codecarbon.external.hardware"]
        except KeyError:
            pass


class TestGpu(FakeGPUEnv):
    def test_is_gpu_details_available(self):
        from codecarbon.core.gpu import is_gpu_details_available

        assert is_gpu_details_available() is True

    def test_static_gpu_info(self):
        from codecarbon.core.gpu import AllGPUDevices

        alldevices = AllGPUDevices()
        expected = [
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid-1",
                "total_memory": 1024,
                "power_limit": 149,
                "gpu_index": 0,
            },
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid-2",
                "total_memory": 1024,
                "power_limit": 149,
                "gpu_index": 1,
            },
        ]

        assert alldevices.get_gpu_static_info() == expected

    def test_gpu_details(self):
        from codecarbon.core.gpu import AllGPUDevices

        alldevices = AllGPUDevices()

        assert alldevices.get_gpu_details() == self.expected

    def test_gpu_no_power_limit(self):
        import pynvml

        from codecarbon.core.gpu import AllGPUDevices

        def raiseException(handle):
            raise Exception("Some bad exception")

        original_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit
        try:
            pynvml.nvmlDeviceGetEnforcedPowerLimit = raiseException
            alldevices = AllGPUDevices()

            expected_power_limit = deepcopy(self.expected)
            expected_power_limit[0]["power_limit"] = None
            expected_power_limit[1]["power_limit"] = None

            assert alldevices.get_gpu_details() == expected_power_limit
        finally:
            pynvml.nvmlDeviceGetEnforcedPowerLimit = original_limit

    def test_gpu_not_ready(self):
        import pynvml

        from codecarbon.core.gpu import AllGPUDevices

        def raise_exception(handle):
            raise pynvml.NVMLError("System is not in ready state")

        original_energy = pynvml.nvmlDeviceGetTotalEnergyConsumption
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = raise_exception
            alldevices = AllGPUDevices()

            expected = deepcopy(self.expected)
            expected[0]["total_energy_consumption"] = None
            expected[1]["total_energy_consumption"] = None

            assert alldevices.get_gpu_details() == expected
        finally:
            pynvml.nvmlDeviceGetTotalEnergyConsumption = original_energy

    def test_gpu_metadata_total_power(self):
        """
        Get the total power of all GPUs
        """
        # Prepare
        from codecarbon.core.units import Energy, Power, Time
        from codecarbon.external.hardware import GPU

        energy_consumption = {
            "handle_0": [100_701, 180_001, 190_001],
            "handle_1": [149_702, 180_002, 200_002],
        }

        def mock_nvmlDeviceGetTotalEnergyConsumption(handle):
            return energy_consumption[handle].pop(0)

        gpu1_energy2 = Energy.from_millijoules(energy_consumption["handle_0"][1])
        gpu1_energy3 = Energy.from_millijoules(energy_consumption["handle_0"][2])
        gpu2_energy2 = Energy.from_millijoules(energy_consumption["handle_1"][1])
        gpu2_energy3 = Energy.from_millijoules(energy_consumption["handle_1"][2])

        gpu2_power2 = Power.from_energies_and_delay(gpu1_energy2, gpu1_energy3, Time(5))
        gpu1_power2 = Power.from_energies_and_delay(gpu2_energy2, gpu2_energy3, Time(5))
        expected_power = gpu1_power2 + gpu2_power2

        with mock.patch(
            "pynvml.nvmlDeviceGetTotalEnergyConsumption",
            side_effect=mock_nvmlDeviceGetTotalEnergyConsumption,
        ):
            gpu = GPU.from_utils()
            gpu.measure_power_and_energy(5)

        assert expected_power.kW == gpu.total_power().kW

    def test_gpu_metadata_one_gpu_power(self):
        """
        Get the power of just one GPU even if there are more than 1
        """
        # Prepare
        from codecarbon.core.units import Energy, Power, Time
        from codecarbon.external.hardware import GPU

        energy_consumption_mock = {
            "handle_0": [100_701, 180_001, 190_001],
            "handle_1": [149_702, 180_002, 200_002],
        }
        energy_consumption = deepcopy(energy_consumption_mock)

        def mock_nvmlDeviceGetTotalEnergyConsumption(handle):
            return energy_consumption_mock[handle].pop(0)

        with mock.patch(
            "pynvml.nvmlDeviceGetTotalEnergyConsumption",
            side_effect=mock_nvmlDeviceGetTotalEnergyConsumption,
        ):
            gpu = GPU.from_utils()
            gpu.measure_power_and_energy(5, gpu_ids=[1])
        print(energy_consumption)
        gpu2_energy1 = Energy.from_millijoules(energy_consumption["handle_1"][1])
        gpu2_energy2 = Energy.from_millijoules(energy_consumption["handle_1"][2])
        gpu2_power = Power.from_energies_and_delay(gpu2_energy1, gpu2_energy2, Time(5))
        expected_power = gpu2_power

        assert expected_power.kW == gpu.total_power().kW

    @mock.patch.dict(
        os.environ,
        {
            "CUDA_VISIBLE_DEVICES": "1",
        },
    )
    def test_gpu_metadata_one_gpu_power_CUDA_VISIBLE_DEVICES(self):
        """
        Get the power of just one GPU even if there are more than 1
        """
        # Prepare
        # (Note: This imports should be inside the test, not on top of the file, otherwise the mock does not work)
        from codecarbon.core.units import Energy, Power, Time
        from codecarbon.external.hardware import GPU

        energy_consumption_mock = {
            "handle_0": [100_000, 100_001, 100_002],
            "handle_1": [149_702, 180_002, 200_002],
        }
        energy_consumption = deepcopy(energy_consumption_mock)

        def mock_nvmlDeviceGetTotalEnergyConsumption(handle):
            # print("mock_nvmlDeviceGetTotalEnergyConsumption", handle, energy_consumption_mock[handle])
            return energy_consumption_mock[handle].pop(0)

        # Call
        with mock.patch(
            "pynvml.nvmlDeviceGetTotalEnergyConsumption",
            side_effect=mock_nvmlDeviceGetTotalEnergyConsumption,  # Mock the energy consumption
        ):
            gpu = GPU.from_utils(gpu_ids=[int(os.environ["CUDA_VISIBLE_DEVICES"])])
            # Despite the fact that there are 2 GPUs, only one is being used
            assert gpu.gpu_ids == [1]
            gpu.measure_power_and_energy(5)

        # Assert
        # ((200_002 - 180_002) * 10 ** (-3)) * 2.77778e-7 * 3_600 /5 = 0.0040000031999999994 kW
        gpu2_energy1 = Energy.from_millijoules(energy_consumption["handle_1"][1])
        gpu2_energy2 = Energy.from_millijoules(energy_consumption["handle_1"][2])
        gpu2_power = Power.from_energies_and_delay(gpu2_energy1, gpu2_energy2, Time(5))
        expected_power = gpu2_power
        tc.assertAlmostEqual(expected_power.kW, gpu.total_power().kW)

    def test_get_gpu_ids(self):
        """
        Check parsing of gpu_ids in various forms.
        """
        # Prepare
        from codecarbon.external.hardware import GPU

        for test_ids, expected_ids in [
            ([0, 1], [0, 1]),
            ([0, 1, 2], [0, 1]),
            ([2], []),
            (["0", "1"], [0, 1]),
            # Only two GPUS in the system, so ignore the third (index 2)
            (["0", "1", "2"], [0, 1]),
            (["2"], []),
            # Check UUID-to-index mapping
            (["uuid-1"], [0]),
            (["uuid-1", "uuid-2"], [0, 1]),
            (["uuid-3"], []),
            # Check UUID-to-index mapping when we need to strip the prefix
            (["MIG-uuid-1"], [0]),
            (["MIG-uuid-3"], []),
        ]:
            gpu = GPU(test_ids)
            result = gpu._get_gpu_ids()
            assert result == expected_ids


class TestGpuNotAvailable:
    def setup_method(self):
        self.old_sys_path = copy(sys.path)
        fake_module_path = os.path.join(os.path.dirname(__file__), "fake_modules")
        sys.path.insert(0, fake_module_path)

        # Clean old modules
        try:
            del sys.modules["pynvml"]
        except KeyError:
            pass

        try:
            del sys.modules["codecarbon.core.gpu"]
        except KeyError:
            pass
        for module_name in (
            "codecarbon.core.gpu_amd",
            "codecarbon.core.gpu_nvidia",
            "codecarbon.core.gpu_device",
        ):
            sys.modules.pop(module_name, None)

        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)

        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)

        import pynvml

        pynvml.INIT_MOCK.side_effect = pynvml.NVMLError("NVML Shared Library Not Found")

    def teardown_method(self):
        import pynvml

        pynvml.INIT_MOCK.reset_mock()

        # Restore the old paths
        sys.path = self.old_sys_path

    def test_is_gpu_details_not_available(self):
        from codecarbon.core.gpu import is_gpu_details_available

        assert is_gpu_details_available() is False

    def test_gpu_details_not_available(self):
        from codecarbon.core.gpu import AllGPUDevices

        alldevices = AllGPUDevices()

        assert alldevices.get_gpu_details() == []

    def test_static_gpu_info_not_available(self):
        from codecarbon.core.gpu import AllGPUDevices

        alldevices = AllGPUDevices()

        assert alldevices.get_gpu_static_info() == []


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
    def test_init_with_no_amd_handles(self, capsys):
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
        ):
            AllGPUDevices()

        captured = capsys.readouterr()
        assert "No AMD GPUs foundon machine" in captured.out

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


class TestGpuImportWarnings:
    def _exec_gpu_module(self, import_func, check_output):
        base_spec = importlib.util.find_spec("codecarbon.core.gpu")
        module_spec = importlib.util.spec_from_file_location(
            "gpu_import_test", base_spec.origin
        )
        module = importlib.util.module_from_spec(module_spec)
        for module_name in (
            "codecarbon.core.gpu",
            "codecarbon.core.gpu_amd",
            "codecarbon.core.gpu_nvidia",
            "codecarbon.core.gpu_device",
        ):
            sys.modules.pop(module_name, None)
        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)
        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)
        with (
            mock.patch("subprocess.check_output", side_effect=check_output),
            mock.patch.object(builtins, "__import__", new=import_func),
        ):
            module_spec.loader.exec_module(module)
        return module

    def test_import_warns_when_modules_missing(self):
        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in ("pynvml", "amdsmi"):
                raise ImportError("missing")
            return real_import(name, globals, locals, fromlist, level)

        def check_output(_cmd, *args, **kwargs):
            return b"ok"

        old_pynvml = sys.modules.pop("pynvml", None)
        old_amdsmi = sys.modules.pop("amdsmi", None)
        try:
            with mock.patch(
                "codecarbon.external.logger.logger.warning"
            ) as warning_mock:
                self._exec_gpu_module(fake_import, check_output)
        finally:
            if old_pynvml is not None:
                sys.modules["pynvml"] = old_pynvml
            if old_amdsmi is not None:
                sys.modules["amdsmi"] = old_amdsmi

        messages = " ".join(str(c.args[0]) for c in warning_mock.call_args_list)
        assert "pynvml is not available" in messages
        assert "amdsmi is not available" in messages

    def test_import_warns_when_pynvml_init_fails(self):
        fake_pynvml = ModuleType("pynvml")

        def nvml_init():
            raise RuntimeError("boom")

        fake_pynvml.nvmlInit = nvml_init
        old_pynvml = sys.modules.get("pynvml")
        sys.modules["pynvml"] = fake_pynvml

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "amdsmi":
                raise ImportError("missing")
            return real_import(name, globals, locals, fromlist, level)

        def check_output(cmd, *args, **kwargs):
            if cmd[0] == "nvidia-smi":
                return b"ok"
            raise OSError("missing")

        try:
            with mock.patch(
                "codecarbon.external.logger.logger.warning"
            ) as warning_mock:
                self._exec_gpu_module(fake_import, check_output)
        finally:
            if old_pynvml is None:
                sys.modules.pop("pynvml", None)
            else:
                sys.modules["pynvml"] = old_pynvml

        assert any(
            "pynvml initialization failed" in str(c.args[0])
            for c in warning_mock.call_args_list
        )

    def test_import_warns_when_amdsmi_attribute_error(self):
        fake_pynvml = ModuleType("pynvml")
        fake_pynvml.nvmlInit = lambda: None
        old_pynvml = sys.modules.get("pynvml")
        sys.modules["pynvml"] = fake_pynvml

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "amdsmi":
                raise AttributeError("broken")
            return real_import(name, globals, locals, fromlist, level)

        def check_output(cmd, *args, **kwargs):
            if cmd[0] == "rocm-smi":
                return b"ok"
            raise OSError("missing")

        try:
            with mock.patch(
                "codecarbon.external.logger.logger.warning"
            ) as warning_mock:
                self._exec_gpu_module(fake_import, check_output)
        finally:
            if old_pynvml is None:
                sys.modules.pop("pynvml", None)
            else:
                sys.modules["pynvml"] = old_pynvml

        assert any(
            "amdsmi is not properly configured" in str(c.args[0])
            for c in warning_mock.call_args_list
        )


class TestGpuMethods:
    @mock.patch("codecarbon.core.gpu_amd.subprocess.check_output")
    def test_is_rocm_system(self, mock_subprocess):
        from codecarbon.core.gpu import is_rocm_system

        mock_subprocess.return_value = b"rocm-smi"
        assert is_rocm_system()

    @mock.patch("codecarbon.core.gpu_amd.subprocess.check_output")
    def test_is_rocm_system_fail(self, mock_subprocess):
        import subprocess

        from codecarbon.core.gpu import is_rocm_system

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert not is_rocm_system()

    @mock.patch("codecarbon.core.gpu_nvidia.subprocess.check_output")
    def test_is_nvidia_system(self, mock_subprocess):
        from codecarbon.core.gpu import is_nvidia_system

        mock_subprocess.return_value = b"nvidia-smi"
        assert is_nvidia_system()

    @mock.patch("codecarbon.core.gpu_nvidia.subprocess.check_output")
    def test_is_nvidia_system_fail(self, mock_subprocess):
        import subprocess

        from codecarbon.core.gpu import is_nvidia_system

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert not is_nvidia_system()


class TestGpuTracking:
    def setup_method(self):
        for module_name in list(sys.modules.keys()):
            if module_name.startswith("codecarbon.core.gpu"):
                sys.modules.pop(module_name, None)
        import codecarbon.core

        for attr in ["gpu", "gpu_nvidia", "gpu_amd", "gpu_device"]:
            if hasattr(codecarbon.core, attr):
                delattr(codecarbon.core, attr)

    @mock.patch("codecarbon.core.gpu.is_rocm_system", return_value=True)
    @mock.patch("codecarbon.core.gpu.is_nvidia_system", return_value=False)
    @mock.patch("codecarbon.core.gpu_amd.subprocess.check_output")
    def test_rocm_initialization(self, mock_subprocess, mock_nvidia, mock_rocm):
        from codecarbon.core.gpu import AllGPUDevices

        # Should not crash on init
        AllGPUDevices()

    @mock.patch("codecarbon.core.gpu.is_rocm_system", return_value=False)
    @mock.patch("codecarbon.core.gpu.is_nvidia_system", return_value=True)
    @mock.patch("codecarbon.core.gpu_nvidia.subprocess.check_output")
    def test_nvidia_initialization(self, mock_subprocess, mock_nvidia, mock_rocm):
        from codecarbon.core.gpu import AllGPUDevices

        # Should not crash on init
        AllGPUDevices()
