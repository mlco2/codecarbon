"""
Tests for backward compatibility with deprecated parameter names.
"""

import unittest
from unittest.mock import patch

from codecarbon.core.carbon_intensity import ElectricityMapsProvider
from codecarbon.emissions_tracker import EmissionsTracker


class TestElectricityMapsBackwardCompatibility(unittest.TestCase):
    """Test that old parameter names still work with deprecation warnings."""

    @patch("os.path.exists", return_value=True)
    def test_tracker_co2_signal_api_token_deprecated(self, mock_exists):
        """Test that co2_signal_api_token parameter works in EmissionsTracker."""

        with self.assertLogs("codecarbon", level="WARNING") as log:
            tracker = EmissionsTracker(co2_signal_api_token="test-token")

        # Check that the token was set correctly, including for the provider
        self.assertEqual(tracker._electricitymaps_api_token, "test-token")
        tracker._ensure_emissions_engine()
        [provider] = tracker._emissions._providers
        self.assertIsInstance(provider, ElectricityMapsProvider)
        self.assertEqual(provider.api_token, "test-token")

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
