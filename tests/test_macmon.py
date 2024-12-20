import os
import unittest
import unittest.result
from unittest import mock

import pytest

from codecarbon.core.macmon import MacMon, is_macmon_available


class TestMacMon(unittest.TestCase):
    @pytest.mark.integ_test
    def test_macmon(self):
        if is_macmon_available():
            power_gadget = MacMon(
                output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
                log_file_name="mock_macmon_log.txt",
            )
            details = power_gadget.get_details()
            assert len(details) > 0

    # @pytest.mark.integ_test
    @mock.patch("codecarbon.core.macmon.MacMon._log_values")
    @mock.patch("codecarbon.core.macmon.MacMon._setup_cli")
    def test_get_details(self, mock_setup, mock_log_values):
        expected_details = {
            "CPU Power": 0.3146,
            "CPU Energy Delta": 0.3146,
            "GPU Power": 0.0386,
            "GPU Energy Delta": 0.0386,
        }
        if is_macmon_available():
            macmon = MacMon(
                output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
                log_file_name="mock_macmon_log.txt",
            )
            cpu_details = macmon.get_details()

            self.assertDictEqual(expected_details, cpu_details)
