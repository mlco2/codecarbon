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
import sys
from types import ModuleType
from unittest import mock


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
