"""
Tests for AWS Inferentia/Inferentia2 Neuron device tracking.
"""

import unittest
from unittest.mock import MagicMock, mock_open, patch


class TestIsNeuronSystem(unittest.TestCase):
    def test_neuron_available(self):
        with patch("os.path.exists", return_value=True):
            from codecarbon.core.neuron import is_neuron_system

            self.assertTrue(is_neuron_system())

    def test_neuron_not_available(self):
        with patch("os.path.exists", return_value=False):
            from codecarbon.core.neuron import is_neuron_system

            self.assertFalse(is_neuron_system())


class TestNeuronDeviceTDP(unittest.TestCase):
    """Tests for _get_max_power_watts() TDP lookup."""

    def _make_device(self, device_path="/fake/neuron0"):
        from codecarbon.core.neuron import NeuronDevice

        with patch("os.path.exists", return_value=False):
            device = NeuronDevice.__new__(NeuronDevice)
            device._device_path = device_path
            device._device_index = 0
            device._max_power_watts = 0.0
        return device

    def test_inf1_device_name(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="inferentia")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 75)

    def test_inf1_shorthand(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="inf1")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 75)

    def test_inf2_device_name(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="inferentia2")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 100)

    def test_inf2_shorthand(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="inf2")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 100)

    def test_uppercase_device_name(self):
        """Device name should be lowercased before lookup."""
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="Inferentia2")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 100)

    def test_unsupported_device(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="trainium1")):
                result = device._get_max_power_watts()
        self.assertEqual(result, 0.0)

    def test_file_not_found(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=False):
            result = device._get_max_power_watts()
        self.assertEqual(result, 0.0)

    def test_exception_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", side_effect=Exception("unexpected")):
            result = device._get_max_power_watts()
        self.assertEqual(result, 0.0)


class TestNeuronDevicePowerFile(unittest.TestCase):
    """Tests for _read_power_file() parsing."""

    def _make_device(self):
        from codecarbon.core.neuron import NeuronDevice

        device = NeuronDevice.__new__(NeuronDevice)
        device._device_path = "/fake/neuron0"
        device._device_index = 0
        device._max_power_watts = 75.0
        return device

    def test_valid_format(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_VALID,1712345678,40.00,80.00,62.50"),
            ):
                result = device._read_power_file()
        self.assertIsNotNone(result)
        status, min_pct, max_pct, avg_pct = result
        self.assertEqual(status, "POWER_STATUS_VALID")
        self.assertAlmostEqual(min_pct, 40.0)
        self.assertAlmostEqual(max_pct, 80.0)
        self.assertAlmostEqual(avg_pct, 62.5)

    def test_no_data_status(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_NO_DATA,1712345678,0.00,0.00,0.00"),
            ):
                result = device._read_power_file()
        status, _, _, _ = result
        self.assertEqual(status, "POWER_STATUS_NO_DATA")

    def test_invalid_status(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_INVALID,1712345678,0.00,0.00,0.00"),
            ):
                result = device._read_power_file()
        status, _, _, _ = result
        self.assertEqual(status, "POWER_STATUS_INVALID")

    def test_file_not_found(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=False):
            result = device._read_power_file()
        self.assertIsNone(result)

    def test_bad_format_returns_none(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="bad_data")):
                result = device._read_power_file()
        self.assertIsNone(result)

    def test_exception_returns_none(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("read error")):
                result = device._read_power_file()
        self.assertIsNone(result)


class TestNeuronDeviceGetPowerWatts(unittest.TestCase):
    """Tests for get_power_watts()."""

    def _make_device(self, tdp=75.0):
        from codecarbon.core.neuron import NeuronDevice

        device = NeuronDevice.__new__(NeuronDevice)
        device._device_path = "/fake/neuron0"
        device._device_index = 0
        device._max_power_watts = tdp
        return device

    def test_valid_inf1(self):
        device = self._make_device(tdp=75.0)
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_VALID,1712345678,40.00,80.00,62.50"),
            ):
                # 62.5% of 75W = 46.875W
                result = device.get_power_watts()
        self.assertAlmostEqual(result, 46.875)

    def test_valid_inf2(self):
        device = self._make_device(tdp=100.0)
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_VALID,1712345678,40.00,80.00,50.00"),
            ):
                # 50% of 100W = 50W
                result = device.get_power_watts()
        self.assertAlmostEqual(result, 50.0)

    def test_no_data_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_NO_DATA,1712345678,0.00,0.00,0.00"),
            ):
                result = device.get_power_watts()
        self.assertEqual(result, 0.0)

    def test_invalid_status_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_INVALID,1712345678,0.00,0.00,0.00"),
            ):
                result = device.get_power_watts()
        self.assertEqual(result, 0.0)

    def test_unknown_tdp_returns_zero(self):
        device = self._make_device(tdp=0.0)
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_VALID,1712345678,40.00,80.00,62.50"),
            ):
                result = device.get_power_watts()
        self.assertEqual(result, 0.0)

    def test_file_not_found_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=False):
            result = device.get_power_watts()
        self.assertEqual(result, 0.0)


class TestNeuronDeviceGetUtilizationPct(unittest.TestCase):
    """Tests for get_utilization_pct()."""

    def _make_device(self):
        from codecarbon.core.neuron import NeuronDevice

        device = NeuronDevice.__new__(NeuronDevice)
        device._device_path = "/fake/neuron0"
        device._device_index = 0
        device._max_power_watts = 75.0
        return device

    def test_valid_returns_avg_pct(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_VALID,1712345678,40.00,80.00,62.50"),
            ):
                result = device.get_utilization_pct()
        self.assertAlmostEqual(result, 62.5)

    def test_no_data_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_NO_DATA,1712345678,0.00,0.00,0.00"),
            ):
                result = device.get_utilization_pct()
        self.assertEqual(result, 0.0)

    def test_invalid_status_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data="POWER_STATUS_INVALID,1712345678,0.00,0.00,0.00"),
            ):
                result = device.get_utilization_pct()
        self.assertEqual(result, 0.0)

    def test_file_not_found_returns_zero(self):
        device = self._make_device()
        with patch("os.path.exists", return_value=False):
            result = device.get_utilization_pct()
        self.assertEqual(result, 0.0)


class TestAllNeuronDevices(unittest.TestCase):
    """Tests for AllNeuronDevices discovery and aggregation."""

    def test_discovers_two_devices(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
                "/fake/neuron_device/neuron1",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.core.neuron import AllNeuronDevices

                    devices = AllNeuronDevices()
        self.assertEqual(devices.device_count, 2)

    def test_no_devices_found(self):
        with patch("glob.glob", return_value=[]):
            from codecarbon.core.neuron import AllNeuronDevices

            devices = AllNeuronDevices()
        self.assertEqual(devices.device_count, 0)

    def test_get_total_power_watts(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
                "/fake/neuron_device/neuron1",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.core.neuron import AllNeuronDevices

                    devices = AllNeuronDevices()
                    for d in devices._devices:
                        d.get_power_watts = MagicMock(return_value=46.875)
        self.assertAlmostEqual(devices.get_total_power_watts(), 93.75)

    def test_get_total_utilization_pct(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
                "/fake/neuron_device/neuron1",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.core.neuron import AllNeuronDevices

                    devices = AllNeuronDevices()
                    devices._devices[0].get_utilization_pct = MagicMock(
                        return_value=60.0
                    )
                    devices._devices[1].get_utilization_pct = MagicMock(
                        return_value=40.0
                    )
        self.assertAlmostEqual(devices.get_total_utilization_pct(), 50.0)

    def test_get_total_utilization_pct_no_devices(self):
        with patch("glob.glob", return_value=[]):
            from codecarbon.core.neuron import AllNeuronDevices

            devices = AllNeuronDevices()
        self.assertEqual(devices.get_total_utilization_pct(), 0.0)

    def test_get_device_details(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.core.neuron import AllNeuronDevices

                    devices = AllNeuronDevices()
                    devices._devices[0].get_power_watts = MagicMock(return_value=46.875)
                    devices._devices[0].get_utilization_pct = MagicMock(
                        return_value=62.5
                    )
        details = devices.get_device_details()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]["device_index"], 0)
        self.assertAlmostEqual(details[0]["power_watts"], 46.875)
        self.assertAlmostEqual(details[0]["utilization_pct"], 62.5)


class TestNeuronChipHardware(unittest.TestCase):
    """Tests for NeuronChip in hardware.py."""

    def test_total_power_no_devices(self):
        with patch("glob.glob", return_value=[]):
            from codecarbon.external.hardware import NeuronChip

            chip = NeuronChip()
            power = chip.total_power()
        self.assertAlmostEqual(power.W, 0.0)

    def test_total_power_with_devices(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.external.hardware import NeuronChip

                    chip = NeuronChip()
                    chip._devices.get_total_power_watts = MagicMock(return_value=46.875)
        power = chip.total_power()
        self.assertAlmostEqual(power.W, 46.875)

    def test_description(self):
        with patch("glob.glob", return_value=[]):
            from codecarbon.external.hardware import NeuronChip

            chip = NeuronChip()
        self.assertIn("Neuron", chip.description())
        self.assertIn("Inferentia", chip.description())

    def test_device_count(self):
        with patch(
            "glob.glob",
            return_value=[
                "/fake/neuron_device/neuron0",
                "/fake/neuron_device/neuron1",
            ],
        ):
            with patch("os.path.isdir", return_value=True):
                with patch("os.path.exists", return_value=False):
                    from codecarbon.external.hardware import NeuronChip

                    chip = NeuronChip()
        self.assertEqual(chip._devices.device_count, 2)


if __name__ == "__main__":
    unittest.main()
