"""Telemetry behaviour as seen through the public ``EmissionsTracker`` path."""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry import Telemetry
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from tests.testutils import (
    ensure_telemetry_run_duration,
    get_custom_mock_open,
    hanging_endpoint,
    join_telemetry,
)

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")

TELEMETRY_ENV_VARS = (
    "CODECARBON_TELEMETRY",
    "CODECARBON_TELEMETRY_LEVEL",
    "CODECARBON_TELEMETRY_API_KEY",
    "CODECARBON_TELEMETRY_API_URL",
)


def _conf(level: str = None, *, api_key: str = "test-key", extra: str = "") -> str:
    conf = "[codecarbon]\n"
    if level is not None:
        conf += f"telemetry_level = {level}\n"
    if api_key is not None:
        conf += f"telemetry_api_key = {api_key}\n"
    return conf + extra


@mock_platform_cli_setup
class TestTrackerTelemetry(unittest.TestCase):
    """Every case goes through the real constructor, not ``resolve()``."""

    def setUp(self) -> None:
        Telemetry._default_warning_shown = False
        self._patchers = []
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() not in TELEMETRY_ENV_VARS
        }
        self._enter(patch.dict(os.environ, clean_env, clear=True))
        self._enter(patch("codecarbon.external.geography.GeoMetadata.from_geo_js"))

    def tearDown(self) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()
        Telemetry._default_warning_shown = False

    def _enter(self, patcher):
        patcher.start()
        self._patchers.append(patcher)
        return patcher

    def _mock_config(self, conf: str) -> None:
        self._enter(
            patch("builtins.open", new_callable=get_custom_mock_open(conf, conf))
        )

    def _mock_post(self):
        return patch(
            "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
        )

    def _run_tracker(self, **kwargs):
        with ensure_telemetry_run_duration():
            tracker = EmissionsTracker(
                measure_power_secs=1, save_to_api=False, save_to_file=False, **kwargs
            )
            tracker.start()
            tracker.stop()
        join_telemetry(tracker)
        return tracker

    def test_no_telemetry_on_init(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            EmissionsTracker(save_to_api=False, save_to_file=False)
        mock_post.assert_not_called()

    def test_minimal_sends_minimal_payload_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            self._run_tracker()
        mock_post.assert_called_once()
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertNotIn("total_emissions_kg", payload)

    def test_config_disabled_sends_nothing(self, mock_cli_setup):
        self._mock_config(_conf("disabled"))
        with self._mock_post() as mock_post:
            self._run_tracker()
        mock_post.assert_not_called()

    def test_kwarg_disabled_overrides_config(self, mock_cli_setup):
        """Regression: ``telemetry_level="disabled"`` used to be ignored entirely."""
        self._mock_config(_conf("extensive"))
        with self._mock_post() as mock_post:
            with patch("codecarbon.core.telemetry.client.ApiClient") as mock_api_cls:
                tracker = self._run_tracker(telemetry_level="disabled")
        mock_post.assert_not_called()
        mock_api_cls.assert_not_called()
        self.assertEqual(tracker._telemetry.settings.level.value, "disabled")
        self.assertEqual(tracker._conf["telemetry_level"], "disabled")

    def test_kwarg_disabled_overrides_env(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY_LEVEL": "extensive"}):
            with self._mock_post() as mock_post:
                self._run_tracker(telemetry_level="disabled")
        mock_post.assert_not_called()

    def test_extensive_also_posts_public_summary(self, mock_cli_setup):
        self._mock_config(_conf("extensive"))
        with self._mock_post() as mock_post:
            with patch("codecarbon.core.telemetry.client.ApiClient") as mock_api_cls:
                mock_api_cls.return_value = MagicMock(
                    **{"add_emission.return_value": True}
                )
                self._run_tracker()
        mock_post.assert_called_once()
        mock_api_cls.assert_called_once()
        self.assertIn("total_emissions_kg", mock_post.call_args[0][1])

    def test_offline_tracker_sends_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            with ensure_telemetry_run_duration():
                tracker = OfflineEmissionsTracker(
                    country_iso_code="CAN", save_to_api=False, save_to_file=False
                )
                tracker.start()
                tracker.stop()
        join_telemetry(tracker)
        mock_post.assert_called_once()

    def test_missing_api_key_sends_nothing(self, mock_cli_setup):
        self._mock_config(_conf("minimal", api_key=None))
        with self._mock_post() as mock_post:
            self._run_tracker()
        mock_post.assert_not_called()

    def test_env_level_overrides_config_file(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY_LEVEL": "disabled"}):
            with self._mock_post() as mock_post:
                self._run_tracker()
        mock_post.assert_not_called()

    def test_legacy_env_var_is_ignored(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY": "disabled"}):
            with self._mock_post() as mock_post:
                self._run_tracker()
        mock_post.assert_called_once()

    def test_api_url_comes_from_config(self, mock_cli_setup):
        self._mock_config(
            _conf("minimal", extra="telemetry_api_url = http://example.test/\n")
        )
        tracker = EmissionsTracker(save_to_api=False, save_to_file=False)
        self.assertEqual(tracker._telemetry.settings.api_url, "http://example.test")

    def test_api_url_comes_from_env(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with patch.dict(
            os.environ, {"CODECARBON_TELEMETRY_API_URL": "http://env.test"}
        ):
            tracker = EmissionsTracker(save_to_api=False, save_to_file=False)
        self.assertEqual(tracker._telemetry.settings.api_url, "http://env.test")

    def test_warns_once_when_level_not_explicit(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            EmissionsTracker(save_to_api=False, save_to_file=False)
            EmissionsTracker(save_to_api=False, save_to_file=False)
        warnings = [
            call
            for call in mock_warning.call_args_list
            if call[0] and "Minimal telemetry" in str(call[0][0])
        ]
        self.assertEqual(len(warnings), 1)

    def _timed_run(self, level: str, url: str):
        """Run a tracker against ``url`` and time ``stop()`` alone."""
        env = {
            "CODECARBON_TELEMETRY_LEVEL": level,
            "CODECARBON_TELEMETRY_API_KEY": "test-key",
            "CODECARBON_TELEMETRY_API_URL": url,
        }
        with patch.dict(os.environ, env), ensure_telemetry_run_duration():
            tracker = OfflineEmissionsTracker(
                country_iso_code="CAN", save_to_api=False, save_to_file=False
            )
            tracker.start()
            start = time.monotonic()
            tracker.stop()
            return tracker, start, time.monotonic() - start

    def test_stop_does_not_block_on_hanging_endpoint(self, mock_cli_setup):
        """``stop()`` hands the send to a daemon thread, so it never waits on IO."""
        with hanging_endpoint() as url:
            # The first stop() in a process pays one-off setup costs unrelated to
            # telemetry, so warm those up before timing anything.
            self._timed_run("disabled", url)
            for level in ("minimal", "extensive"):
                with self.subTest(level=level):
                    tracker, start, elapsed = self._timed_run(level, url)
                    thread = tracker._telemetry._thread
                    self.assertIsNotNone(thread)
                    # Synchronously this cost 2s (minimal) to 6s (extensive).
                    self.assertLess(elapsed, 0.5)
                    # One budget for the whole send, however many requests it makes.
                    thread.join(20)
                    self.assertFalse(thread.is_alive())
                    self.assertLess(time.monotonic() - start, 4.0)

    def test_no_warning_when_level_set_by_kwarg(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            EmissionsTracker(
                telemetry_level="disabled", save_to_api=False, save_to_file=False
            )
        warnings = [
            call
            for call in mock_warning.call_args_list
            if call[0] and "Minimal telemetry" in str(call[0][0])
        ]
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
