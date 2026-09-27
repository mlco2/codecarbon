"""Telemetry behaviour as seen through the public ``EmissionsTracker`` path."""

import os
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
    "CODECARBON_TELEMETRY_API_URL",
)


def _conf(level: str = None, *, extra: str = "") -> str:
    conf = "[codecarbon]\n"
    if level is not None:
        conf += f"telemetry_level = {level}\n"
    return conf + extra


@mock_platform_cli_setup
class TestTrackerTelemetry(unittest.TestCase):
    """Every case goes through the real constructor, not ``resolve()``."""

    def setUp(self) -> None:
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

    def test_sends_once_per_process(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            self._run_tracker()
            self._run_tracker()
        mock_post.assert_called_once()

    def test_short_run_does_not_use_up_the_single_send(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            tracker = EmissionsTracker(save_to_api=False, save_to_file=False)
            tracker._telemetry.send_at_stop(tracker, SimpleNamespace(duration=0.5))
            join_telemetry(tracker)
            mock_post.assert_not_called()
            self._run_tracker()
        mock_post.assert_called_once()

    def test_config_disabled_sends_nothing(self, mock_cli_setup):
        self._mock_config(_conf("disabled"))
        with self._mock_post() as mock_post:
            self._run_tracker()
        mock_post.assert_not_called()

    def test_kwarg_disabled_overrides_config(self, mock_cli_setup):
        """Regression: ``telemetry_level="disabled"`` used to be ignored entirely."""
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            tracker = self._run_tracker(telemetry_level="disabled")
        mock_post.assert_not_called()
        self.assertEqual(tracker._telemetry.settings.level.value, "disabled")
        self.assertNotIn("telemetry_level", tracker._conf)

    def test_kwarg_disabled_overrides_env(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY_LEVEL": "minimal"}):
            with self._mock_post() as mock_post:
                self._run_tracker(telemetry_level="disabled")
        mock_post.assert_not_called()

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

    def _notices(self, mock_warning):
        return [
            call
            for call in mock_warning.call_args_list
            if call[0] and "telemetry is on by default" in str(call[0][0])
        ]

    def test_notice_once_per_machine_when_level_not_explicit(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            EmissionsTracker(save_to_api=False, save_to_file=False)
            EmissionsTracker(save_to_api=False, save_to_file=False)
        notices = self._notices(mock_warning)
        self.assertEqual(len(notices), 1)

    def test_payload_built_off_the_stop_thread(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with (
            self._mock_post(),
            patch(
                "codecarbon.core.telemetry.dispatcher.build_payload", return_value={}
            ) as mock_build,
        ):
            with ensure_telemetry_run_duration():
                tracker = EmissionsTracker(
                    measure_power_secs=1, save_to_api=False, save_to_file=False
                )
                tracker.start()
                with patch(
                    "codecarbon.core.telemetry.dispatcher.threading.Thread.start"
                ):
                    tracker.stop()
        mock_build.assert_not_called()

    def _timed_run(self, level: str, url: str):
        """Run a tracker against ``url`` and time ``stop()`` alone."""
        env = {
            "CODECARBON_TELEMETRY_LEVEL": level,
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
            tracker, start, elapsed = self._timed_run("minimal", url)
            thread = tracker._telemetry._thread
            self.assertIsNotNone(thread)
            # Synchronously this cost the full 2s request timeout.
            self.assertLess(elapsed, 0.5)
            # The send itself gives up once its time budget is spent.
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
        self.assertEqual(self._notices(mock_warning), [])


class TestDispatcherEdges(unittest.TestCase):
    def _telemetry(self):
        from codecarbon.core.telemetry.dispatcher import Telemetry
        from codecarbon.core.telemetry.settings import TelemetrySettings

        return Telemetry(TelemetrySettings.resolve(external_conf={}))

    def test_send_failure_is_swallowed(self):
        from codecarbon.core.telemetry import dispatcher

        with (
            patch.object(dispatcher, "build_payload", side_effect=RuntimeError),
            patch.object(dispatcher, "post_private") as mock_post,
        ):
            self._telemetry()._send(SimpleNamespace(), SimpleNamespace())
        mock_post.assert_not_called()

    def test_notice_still_shown_when_marker_cannot_be_written(self):
        from codecarbon.core.telemetry import dispatcher

        marker = MagicMock()
        marker.exists.side_effect = OSError("read-only")
        with (
            patch.object(dispatcher, "NOTICE_MARKER", marker),
            patch.object(dispatcher.logger, "warning") as mock_warning,
        ):
            self._telemetry().notice_once_if_implicit()
        mock_warning.assert_called_once()

    def test_exit_joins_pending_sends(self):
        from codecarbon.core.telemetry import dispatcher

        thread = MagicMock()
        thread.is_alive.return_value = True
        with patch.object(dispatcher, "_pending", {thread}):
            dispatcher._join_pending()
        thread.join.assert_called_once()


class TestTelemetrySettings(unittest.TestCase):
    def test_enum_level_passes_through(self):
        from codecarbon.core.telemetry.schemas import TelemetryLevel
        from codecarbon.core.telemetry.settings import parse_telemetry_level

        self.assertIs(
            parse_telemetry_level(TelemetryLevel.disabled), TelemetryLevel.disabled
        )

    def test_invalid_level_falls_back_to_minimal(self):
        from codecarbon.core.telemetry.settings import TelemetrySettings

        with patch("codecarbon.core.telemetry.settings.logger") as mock_logger:
            settings = TelemetrySettings.resolve(
                external_conf={"telemetry_level": "extensive"}
            )
        self.assertEqual(settings.level.value, "minimal")
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
