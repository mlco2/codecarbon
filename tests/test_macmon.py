import os
import statistics
import subprocess
from unittest import mock

import pytest

from codecarbon.core import macmon as macmon_module
from codecarbon.core.macmon import MacMon, clear_macmon_cache, is_macmon_available

MOCK_LOG = os.path.join(os.path.dirname(__file__), "test_data", "mock_macmon_log.txt")


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_macmon_cache()
    yield
    clear_macmon_cache()


def _apple_silicon(cpu_model="Apple M1", which="/opt/homebrew/bin/macmon"):
    return (
        mock.patch.object(macmon_module.sys, "platform", "darwin"),
        mock.patch.object(macmon_module, "detect_cpu_model", return_value=cpu_model),
        mock.patch.object(macmon_module.shutil, "which", return_value=which),
    )


def _make_macmon(**kwargs):
    platform, model, which = _apple_silicon()
    with platform, model, which:
        return MacMon(**kwargs)


class FakeProcess:
    def __init__(self, stdout="", stderr="", returncode=0, timeout=False):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self._timeout = timeout
        self.killed = False
        self.stdout = None
        self.stderr = None

    def communicate(self, timeout=None):
        if self._timeout:
            raise subprocess.TimeoutExpired(cmd="macmon", timeout=timeout)
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return self.returncode


def test_is_macmon_available_on_apple_silicon_with_macmon():
    platform, model, which = _apple_silicon()
    with platform, model, which:
        assert is_macmon_available() is True


@pytest.mark.parametrize(
    "platform, cpu_model, which",
    [
        ("linux", "Apple M1", "/usr/bin/macmon"),
        ("darwin", "Intel(R) Core(TM) i7", "/usr/local/bin/macmon"),
        ("darwin", None, "/usr/local/bin/macmon"),
        ("darwin", "Apple M3", None),
    ],
)
def test_is_macmon_available_false(platform, cpu_model, which):
    with (
        mock.patch.object(macmon_module.sys, "platform", platform),
        mock.patch.object(macmon_module, "detect_cpu_model", return_value=cpu_model),
        mock.patch.object(macmon_module.shutil, "which", return_value=which),
    ):
        assert is_macmon_available() is False


def test_is_macmon_available_does_not_run_macmon():
    platform, model, which = _apple_silicon()
    with (
        platform,
        model,
        which,
        mock.patch.object(macmon_module.subprocess, "Popen") as mock_popen,
    ):
        is_macmon_available()
    mock_popen.assert_not_called()


def test_get_details_averages_samples():
    with open(MOCK_LOG) as f:
        stdout = f.read()
    macmon = _make_macmon(n_points=10, interval=100)

    with mock.patch.object(
        macmon_module.subprocess, "Popen", return_value=FakeProcess(stdout=stdout)
    ) as mock_popen:
        details = macmon.get_details()

    cmd = mock_popen.call_args.args[0]
    assert cmd == ["/opt/homebrew/bin/macmon", "pipe", "-s", "10", "-i", "100"]

    cpu = [0.47729987, 0.43330622, 0.17238411, 0.1759564, 0.20275298]
    cpu += [0.21767727, 0.86930436, 0.22681558, 0.5067222, 0.7002688]
    assert details["CPU Power"] == pytest.approx(statistics.fmean(cpu))
    # 10 samples of 0.1 s: energy in joules is the sum of the samples / 10
    assert details["CPU Energy Delta"] == pytest.approx(sum(cpu) * 0.1)
    assert details["GPU Power"] == pytest.approx(0.0321656683)
    assert set(details) == {
        "CPU Power",
        "CPU Energy Delta",
        "GPU Power",
        "GPU Energy Delta",
    }


def test_get_details_ignores_non_json_lines():
    stdout = 'warning: something\n{"cpu_power": 2.0, "gpu_power": 1.0}\n\n'
    macmon = _make_macmon()
    with mock.patch.object(
        macmon_module.subprocess, "Popen", return_value=FakeProcess(stdout=stdout)
    ):
        details = macmon.get_details()
    assert details["CPU Power"] == 2.0
    assert details["GPU Power"] == 1.0


def test_get_details_returns_empty_on_error_code():
    macmon = _make_macmon()
    with mock.patch.object(
        macmon_module.subprocess,
        "Popen",
        return_value=FakeProcess(returncode=1, stderr="boom"),
    ):
        assert macmon.get_details() == {}


def test_get_details_returns_empty_on_timeout():
    macmon = _make_macmon()
    process = FakeProcess(timeout=True)
    with mock.patch.object(macmon_module.subprocess, "Popen", return_value=process):
        assert macmon.get_details() == {}
    assert process.killed is True


def test_get_details_returns_empty_without_samples():
    macmon = _make_macmon()
    with mock.patch.object(
        macmon_module.subprocess, "Popen", return_value=FakeProcess(stdout="")
    ):
        assert macmon.get_details() == {}


@pytest.mark.integ_test
def test_macmon_on_real_hardware():
    if not is_macmon_available():
        pytest.skip("macmon is not available on this machine")
    details = MacMon(n_points=2, interval=100).get_details()
    assert details["CPU Power"] >= 0
