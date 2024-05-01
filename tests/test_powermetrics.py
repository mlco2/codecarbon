import os
import unittest
import unittest.result
from unittest import mock

import pytest

from codecarbon.core.powermetrics import ApplePowermetrics, is_powermetrics_available


class TestApplePowerMetrics(unittest.TestCase):

    @pytest.mark.integ_test
    def test_apple_powermetrics(self):
        if is_powermetrics_available():
            power_gadget = ApplePowermetrics()
            details = power_gadget.get_details()
            assert len(details) > 0

    # @pytest.mark.integ_test
    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._log_values")
    @mock.patch("codecarbon.core.powermetrics.ApplePowermetrics._setup_cli")
    def test_get_details(self, mock_setup, mock_log_values):
        expected_details = {
            "CPU Power": 0.3146,
            "CPU Energy Delta": 0.3146,
            "GPU Power": 0.0386,
            "GPU Energy Delta": 0.0386,
        }
        if is_powermetrics_available():
            powermetrics = ApplePowermetrics(
                output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
                log_file_name="mock_powermetrics_log.txt",
            )
            cpu_details = powermetrics.get_details()

            self.assertDictEqual(expected_details, cpu_details)
