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

import os.path
import sys
from copy import copy, deepcopy

import pynvml as real_pynvml


class FakeGPUEnv(object):
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

        # Setup the state, strings are returned as bytes
        self.DETAILS = {
            "handle_0": {
                "name": b"GeForce GTX 1080",
                "uuid": b"uuid#1",
                "memory": real_pynvml.c_nvmlMemory_t(1024, 100, 924),
                "temperature": 75,
                "power_usage": 26,
                "power_limit": 149,
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
                "uuid": b"uuid#2",
                "memory": real_pynvml.c_nvmlMemory_t(1024, 200, 824),
                "temperature": 79,
                "power_usage": 29,
                "power_limit": 149,
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
                "uuid": "uuid#1",
                "total_memory": 1024,
                "free_memory": 100,
                "used_memory": 924,
                "temperature": 75,
                "power_usage": 26,
                "power_limit": 149,
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
                "uuid": "uuid#2",
                "total_memory": 1024,
                "free_memory": 200,
                "used_memory": 824,
                "temperature": 79,
                "power_usage": 29,
                "power_limit": 149,
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


class TestGpu(FakeGPUEnv):
    def test_is_gpu_details_available(self):
        from codecarbon.core.gpu import is_gpu_details_available

        assert is_gpu_details_available() is True

    def test_static_gpu_info(self):
        from codecarbon.core.gpu import get_gpu_static_info

        expected = [
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid#1",
                "total_memory": 1024,
                "power_limit": 149,
                "gpu_index": 0,
            },
            {
                "name": "GeForce GTX 1080",
                "uuid": "uuid#2",
                "total_memory": 1024,
                "power_limit": 149,
                "gpu_index": 1,
            },
        ]

        assert get_gpu_static_info() == expected

    def test_gpu_details(self):
        from codecarbon.core.gpu import get_gpu_details

        assert get_gpu_details() == self.expected

    def test_gpu_no_power_limit(self):
        import pynvml

        from codecarbon.core.gpu import get_gpu_details

        def raiseException(handle):
            raise Exception("Some bad exception")

        pynvml.nvmlDeviceGetEnforcedPowerLimit = raiseException

        expected_power_limit = deepcopy(self.expected)
        expected_power_limit[0]["power_limit"] = None
        expected_power_limit[1]["power_limit"] = None

        assert get_gpu_details() == expected_power_limit


class TestGpuNotAvailable(object):
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
        from codecarbon.core.gpu import get_gpu_details

        assert get_gpu_details() == []

    def test_static_gpu_info_not_available(self):
        from codecarbon.core.gpu import get_gpu_static_info

        assert get_gpu_static_info() == []
