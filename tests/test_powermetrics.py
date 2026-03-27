import os
from unittest import mock

import pytest

from codecarbon.core import powermetrics as powermetrics_module
from codecarbon.core.powermetrics import ApplePowermetrics, is_powermetrics_available


class FakeProcess:
    def __init__(self, stderr="", returncode=0):
        self._stderr = stderr
        self.returncode = returncode

    def communicate(self):
        return ("", self._stderr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestApplePowerMetrics:
    @pytest.mark.integ_test
    def test_apple_powermetrics(self):
        if is_powermetrics_available():
            power_gadget = ApplePowermetrics()
            details = power_gadget.get_details()
            assert len(details) > 0

    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._log_values")
    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._setup_cli")
    def test_get_details(self, mock_setup, mock_log_values):
        expected_details = {
            "CPU Power": 0.3146,
            "CPU Energy Delta": 0.3146,
            "GPU Power": 0.0386,
            "GPU Energy Delta": 0.0386,
        }
        powermetrics = ApplePowermetrics(
            output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
            log_file_name="mock_powermetrics_log.txt",
        )
        cpu_details = powermetrics.get_details()

        assert cpu_details == expected_details

    def test_is_powermetrics_available_returns_false_on_instantiation_error(self):
        with mock.patch(
            "codecarbon.core.powermetrics.ApplePowermetrics",
            side_effect=Exception("boom"),
        ):
            assert is_powermetrics_available() is False

    def test_has_powermetrics_sudo_returns_false_when_sudo_missing(self):
        with mock.patch("codecarbon.core.powermetrics.shutil.which", return_value=None):
            assert powermetrics_module._has_powermetrics_sudo() is False

    def test_has_powermetrics_sudo_returns_false_when_powermetrics_missing(self):
        with mock.patch(
            "codecarbon.core.powermetrics.shutil.which",
            side_effect=["sudo-path", None],
        ):
            assert powermetrics_module._has_powermetrics_sudo() is False

    def test_has_powermetrics_sudo_returns_false_on_password_prompt(self):
        with (
            mock.patch(
                "codecarbon.core.powermetrics.shutil.which",
                side_effect=["sudo-path", "powermetrics-path"],
            ),
            mock.patch(
                "codecarbon.core.powermetrics.subprocess.Popen",
                return_value=FakeProcess(stderr="[sudo] password for user:", returncode=0),
            ),
        ):
            assert powermetrics_module._has_powermetrics_sudo() is False

    def test_has_powermetrics_sudo_raises_on_nonzero_returncode(self):
        with (
            mock.patch(
                "codecarbon.core.powermetrics.shutil.which",
                side_effect=["sudo-path", "powermetrics-path"],
            ),
            mock.patch(
                "codecarbon.core.powermetrics.subprocess.Popen",
                return_value=FakeProcess(stderr="", returncode=1),
            ),
        ):
            with pytest.raises(Exception, match="Return code != 0"):
                powermetrics_module._has_powermetrics_sudo()

    def test_has_powermetrics_sudo_returns_true_on_success(self):
        with (
            mock.patch(
                "codecarbon.core.powermetrics.shutil.which",
                side_effect=["sudo-path", "powermetrics-path"],
            ),
            mock.patch(
                "codecarbon.core.powermetrics.subprocess.Popen",
                return_value=FakeProcess(stderr="", returncode=0),
            ),
        ):
            assert powermetrics_module._has_powermetrics_sudo() is True

    def test_setup_cli_raises_on_unsupported_platform(self):
        with mock.patch.object(ApplePowermetrics, "_setup_cli", ApplePowermetrics._setup_cli):
            with mock.patch("codecarbon.core.powermetrics.sys.platform", "win32"):
                with pytest.raises(SystemError):
                    ApplePowermetrics()

    def test_setup_cli_raises_when_binary_missing_on_apple_silicon(self):
        with (
            mock.patch("codecarbon.core.powermetrics.sys.platform", "darwin"),
            mock.patch("codecarbon.core.powermetrics.detect_cpu_model", return_value="Apple M4"),
            mock.patch("codecarbon.core.powermetrics.shutil.which", return_value=None),
        ):
            with pytest.raises(FileNotFoundError):
                ApplePowermetrics()

    def test_log_values_returns_none_on_non_darwin(self):
        powermetrics = ApplePowermetrics.__new__(ApplePowermetrics)
        powermetrics._system = "linux"

        assert powermetrics._log_values() is None

    def test_log_values_warns_on_nonzero_returncode(self):
        powermetrics = ApplePowermetrics.__new__(ApplePowermetrics)
        powermetrics._system = "darwin"
        powermetrics._n_points = 3
        powermetrics._interval = 100
        powermetrics._log_file_path = "powermetrics_log.txt"

        with (
            mock.patch("codecarbon.core.powermetrics.subprocess.call", return_value=1) as mock_call,
            mock.patch("codecarbon.core.powermetrics.logger.warning") as mock_warning,
        ):
            powermetrics._log_values()

        mock_call.assert_called_once()
        mock_warning.assert_called_once()

    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._log_values")
    @mock.patch("builtins.open", side_effect=OSError("missing"))
    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._setup_cli")
    def test_get_details_returns_empty_dict_on_read_error(
        self, mock_setup, mock_open, mock_log_values
    ):
        powermetrics = ApplePowermetrics(output_dir=".", log_file_name="missing.txt")

        assert powermetrics.get_details() == {}
