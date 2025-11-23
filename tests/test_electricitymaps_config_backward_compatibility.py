"""
Test backward compatibility with configuration files using old parameter names.
"""

import unittest
from textwrap import dedent
from unittest.mock import patch

from codecarbon.emissions_tracker import EmissionsTracker
from tests.testutils import get_custom_mock_open


class TestConfigBackwardCompatibility(unittest.TestCase):
    """Test that old config parameter names still work."""

    @patch("os.path.exists", return_value=True)
    def test_old_config_parameter_name(self, mock_exists):
        """Test that co2_signal_api_token in config file still works."""
        config_with_old_name = dedent(
            """\
            [codecarbon]
            co2_signal_api_token=old-config-token
            """
        )

        with patch(
            "builtins.open", new_callable=get_custom_mock_open(config_with_old_name, "")
        ):
            with self.assertLogs("codecarbon", level="WARNING") as log:
                tracker = EmissionsTracker()

            # Should use the token from config
            self.assertEqual(tracker._electricitymaps_api_token, "old-config-token")

            # Should warn about deprecated config parameter
            self.assertTrue(
                any("deprecated" in message.lower() for message in log.output),
                "Expected deprecation warning for config parameter",
            )


    @patch("os.path.exists", return_value=True)
    def test_new_config_parameter_takes_precedence(self, mock_exists):
        """Test that new config parameter takes precedence over old one."""
        config_with_both_names = dedent(
            """\
            [codecarbon]
            electricitymaps_api_token=new-config-token
            co2_signal_api_token=old-config-token
            """
        )

        with patch(
            "builtins.open",
            new_callable=get_custom_mock_open(config_with_both_names, ""),
        ):
            tracker = EmissionsTracker()

            # New parameter should take precedence
            self.assertEqual(tracker._electricitymaps_api_token, "new-config-token")



if __name__ == "__main__":
    unittest.main()
