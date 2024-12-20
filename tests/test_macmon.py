import os
import unittest
import unittest.result
from unittest import mock

import numpy as np
import pytest

from codecarbon.core.macmon import MacMon, is_macmon_available


class TestMacMon(unittest.TestCase):
    @pytest.mark.integ_test
    def test_macmon(self):
        if is_macmon_available():
            output_dir = os.path.join(os.path.dirname(__file__), "test_data")
            log_file_path = os.path.join(output_dir, "macmon_log.txt")
            power_gadget = MacMon(
                output_dir=output_dir,
                log_file_name="macmon_log.txt",
            )
            details = power_gadget.get_details()

            assert len(details) > 0

            # Cleanup
            if os.path.exists(log_file_path):
                os.remove(log_file_path)

    # @pytest.mark.integ_test
    @mock.patch("codecarbon.core.macmon.MacMon._log_values")
    @mock.patch("codecarbon.core.macmon.MacMon._setup_cli")
    def test_get_details(self, mock_setup, mock_log_values):
        expected_details = {
            "CPU Power": np.float64(0.000398248779),
            "CPU Energy Delta": np.float64(0.000398248779),
            "GPU Power": np.float64(3.21656683e-05),
            "GPU Energy Delta": np.float64(3.2165668299999997e-05),
            "Ram Power": np.float64(0.0),
            "Ram Energy Delta": np.float64(0.0),
        }
        if is_macmon_available():
            macmon = MacMon(
                output_dir=os.path.join(os.path.dirname(__file__), "test_data"),
                log_file_name="mock_macmon_log.txt",
            )
            details = macmon.get_details()

            self.assertDictEqual(expected_details, details)
