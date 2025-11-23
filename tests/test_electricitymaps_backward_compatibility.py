"""
Tests for backward compatibility with deprecated parameter names.
"""

import unittest
from unittest.mock import patch

from codecarbon.core.emissions import Emissions
from codecarbon.emissions_tracker import EmissionsTracker
from codecarbon.input import DataSource


class TestElectricityMapsBackwardCompatibility(unittest.TestCase):
    """Test that old parameter names still work with deprecation warnings."""

    def test_emissions_co2_signal_api_token_deprecated(self):
        """Test that co2_signal_api_token still works in Emissions class."""
        data_source = DataSource()

        # Using the old parameter name should emit a warning
        with self.assertLogs("codecarbon", level="WARNING") as log:
            emissions = Emissions(data_source, co2_signal_api_token="test-token")

        # Check that the token was set correctly
        self.assertEqual(emissions._electricitymaps_api_token, "test-token")

        # Check that a deprecation warning was logged
        self.assertTrue(
            any("deprecated" in message.lower() for message in log.output),
            "Expected deprecation warning not found",
        )

    def test_emissions_new_parameter_takes_precedence(self):
        """Test that new parameter takes precedence over old one."""
        data_source = DataSource()

        with self.assertLogs("codecarbon", level="WARNING"):
            emissions = Emissions(
                data_source,
                electricitymaps_api_token="new-token",
                co2_signal_api_token="old-token",
            )

        # New parameter should take precedence
        self.assertEqual(emissions._electricitymaps_api_token, "new-token")

    @patch("os.path.exists", return_value=True)
    def test_tracker_co2_signal_api_token_deprecated(self, mock_exists):
        """Test that co2_signal_api_token parameter works in EmissionsTracker."""

        with self.assertLogs("codecarbon", level="WARNING") as log:
            tracker = EmissionsTracker(co2_signal_api_token="test-token")

        # Check that the token was set correctly
        self.assertEqual(tracker._electricitymaps_api_token, "test-token")

        # Check that a deprecation warning was logged
        self.assertTrue(
            any("deprecated" in message.lower() for message in log.output),
            "Expected deprecation warning not found",
        )

    @patch("os.path.exists", return_value=True)
    def test_tracker_new_parameter_takes_precedence(self, mock_exists):
        """Test that new parameter takes precedence in EmissionsTracker."""

        with self.assertLogs("codecarbon", level="WARNING") as log:
            tracker = EmissionsTracker(
                electricitymaps_api_token="new-token", co2_signal_api_token="old-token"
            )

        # New parameter should take precedence
        self.assertEqual(tracker._electricitymaps_api_token, "new-token")

        # Still should warn about using deprecated parameter
        self.assertTrue(any("deprecated" in message.lower() for message in log.output))


if __name__ == "__main__":
    unittest.main()
