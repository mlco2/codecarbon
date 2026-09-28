"""Telemetry behaviour as seen through the public ``EmissionsTracker`` path."""

import os
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from codecarbon.core.telemetry.dispatcher import Telemetry
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

    def test_offline_tracker_never_sends_telemetry(self, mock_cli_setup):
        """Offline mode is chosen for no-network runs: it must never call out,
        including for telemetry, even when the config/env would otherwise
        enable it.
        """
        self._mock_config(_conf("minimal"))
        with self._mock_post() as mock_post:
            with ensure_telemetry_run_duration():
                tracker = OfflineEmissionsTracker(
                    country_iso_code="CAN", save_to_api=False, save_to_file=False
                )
                self.assertEqual(tracker._telemetry.settings.level.value, "disabled")
                tracker.start()
                tracker.stop()
            join_telemetry(tracker)
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

    def _notices(self, mock_warning):
        return [
            call
            for call in mock_warning.call_args_list
            if call[0] and "telemetry is on by default" in str(call[0][0])
        ]

    def test_notice_printed_to_stderr_even_at_default_log_level(self, mock_cli_setup):
        """``codecarbon monitor`` defaults to log_level=error, which hides a
        WARNING-only notice; the notice must be visible regardless of log level.
        """
        self._mock_config(_conf())
        with patch("sys.stderr") as mock_stderr:
            EmissionsTracker(save_to_api=False, save_to_file=False, log_level="error")
        printed = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        self.assertIn("telemetry is on by default", printed)

    def test_notice_once_per_process_when_level_not_explicit(self, mock_cli_setup):
        self._mock_config(_conf())
        with patch("codecarbon.core.telemetry.dispatcher.logger.debug") as mock_debug:
            EmissionsTracker(save_to_api=False, save_to_file=False)
            EmissionsTracker(save_to_api=False, save_to_file=False)
        notices = self._notices(mock_debug)
        self.assertEqual(len(notices), 1)

    def test_notice_logged_at_debug_not_warning(self, mock_cli_setup):
        """The notice is printed to stderr once; it must not also be logged
        at WARNING, or it would show twice at warning-or-lower log levels."""
        self._mock_config(_conf())
        with (
            patch("sys.stderr"),
            patch(
                "codecarbon.core.telemetry.dispatcher.logger.warning"
            ) as mock_warning,
        ):
            EmissionsTracker(save_to_api=False, save_to_file=False)
        self.assertEqual(self._notices(mock_warning), [])

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
            # Offline mode never sends telemetry (see
            # test_offline_tracker_never_sends_telemetry); this test is only
            # about the generic non-blocking behaviour of a send, so it
            # re-enables telemetry on this instance directly.
            from codecarbon.core.telemetry.schemas import TelemetryLevel
            from codecarbon.core.telemetry.settings import TelemetrySettings

            tracker._telemetry = Telemetry(
                TelemetrySettings(
                    level=TelemetryLevel(level),
                    is_explicit=True,
                    api_url=url,
                )
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

    def test_notice_shown_once_per_process_even_across_trackers(self):
        """Many trackers in one process must only print the notice once."""
        from codecarbon.core.telemetry import dispatcher

        with patch.object(dispatcher.logger, "debug") as mock_debug:
            self._telemetry().notice_once_if_implicit()
            self._telemetry().notice_once_if_implicit()
        mock_debug.assert_called_once()

    def test_notice_shown_again_in_a_fresh_process(self):
        """A new process (simulated by ``_reset_after_fork``) sees it again."""
        from codecarbon.core.telemetry import dispatcher

        with patch.object(dispatcher.logger, "debug") as mock_debug:
            self._telemetry().notice_once_if_implicit()
            dispatcher._reset_after_fork()
            self._telemetry().notice_once_if_implicit()
        self.assertEqual(mock_debug.call_count, 2)

    def test_notice_never_shown_when_level_explicit(self):
        from codecarbon.core.telemetry import dispatcher
        from codecarbon.core.telemetry.settings import TelemetrySettings

        telemetry = dispatcher.Telemetry(
            TelemetrySettings.resolve(external_conf={}, override="minimal")
        )
        with patch.object(dispatcher.logger, "warning") as mock_warning:
            telemetry.notice_once_if_implicit()
        mock_warning.assert_not_called()

    def test_notice_never_shown_when_disabled(self):
        from codecarbon.core.telemetry import dispatcher
        from codecarbon.core.telemetry.settings import TelemetrySettings

        telemetry = dispatcher.Telemetry(
            TelemetrySettings.resolve(external_conf={"telemetry_level": "disabled"})
        )
        with patch.object(dispatcher.logger, "warning") as mock_warning:
            telemetry.notice_once_if_implicit()
        mock_warning.assert_not_called()

    def test_exit_joins_pending_sends(self):
        from codecarbon.core.telemetry import dispatcher

        thread = MagicMock()
        thread.is_alive.return_value = True
        with patch.object(dispatcher, "_pending", {thread}):
            dispatcher._join_pending()
        thread.join.assert_called_once()

    def test_thread_start_failure_does_not_crash_stop(self):
        """A broken thread creation/start must never propagate out of stop()."""
        from codecarbon.core.telemetry import dispatcher

        with (
            patch.object(dispatcher, "_sent", False),
            patch.object(
                dispatcher.threading, "Thread", side_effect=RuntimeError("boom")
            ),
        ):
            telemetry = self._telemetry()
            telemetry.send_at_stop(
                SimpleNamespace(), SimpleNamespace(duration=5)
            )  # must not raise
        self.assertFalse(dispatcher._sent)

    def test_sent_marked_only_after_thread_actually_started(self):
        from codecarbon.core.telemetry import dispatcher

        started = []
        real_thread_cls = dispatcher.threading.Thread

        class TrackingThread(real_thread_cls):
            def start(self):
                started.append(dispatcher._sent)
                super().start()

        with (
            patch.object(dispatcher, "_sent", False),
            patch.object(dispatcher.threading, "Thread", TrackingThread),
        ):
            telemetry = self._telemetry()
            telemetry.send_at_stop(SimpleNamespace(), SimpleNamespace(duration=5))
            telemetry._thread.join(5)
            # _sent was still False at the moment start() was called.
            self.assertEqual(started, [False])
            self.assertTrue(dispatcher._sent)

    def test_fork_reset_clears_sent_flag_and_lock(self):
        from codecarbon.core.telemetry import dispatcher

        dispatcher._sent = True
        old_lock = dispatcher._sent_lock
        try:
            dispatcher._reset_after_fork()
            self.assertFalse(dispatcher._sent)
            self.assertIsNot(dispatcher._sent_lock, old_lock)
        finally:
            dispatcher._sent = False


class TestTelemetrySettings(unittest.TestCase):
    def test_enum_level_passes_through(self):
        from codecarbon.core.telemetry.schemas import TelemetryLevel
        from codecarbon.core.telemetry.settings import parse_telemetry_level

        self.assertIs(
            parse_telemetry_level(TelemetryLevel.disabled), TelemetryLevel.disabled
        )

    def test_legacy_extensive_level_maps_to_minimal(self):
        from codecarbon.core.telemetry.settings import TelemetrySettings

        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_level": "extensive"}
        )
        self.assertEqual(settings.level.value, "minimal")

    def test_unparseable_level_falls_back_to_disabled(self):
        from codecarbon.core.telemetry.schemas import TelemetryLevel
        from codecarbon.core.telemetry.settings import TelemetrySettings

        with patch("codecarbon.core.telemetry.settings.logger") as mock_logger:
            settings = TelemetrySettings.resolve(
                external_conf={"telemetry_level": "bogus"}
            )
        self.assertIs(settings.level, TelemetryLevel.disabled)
        mock_logger.error.assert_called_once()

    def test_api_endpoint_config_key_is_not_used_for_telemetry_url(self):
        """``api_endpoint`` configures the dashboard experiment API
        (``save_to_api``), a separate concern from telemetry; it must never
        redirect telemetry to that host.
        """
        from codecarbon.core.telemetry.settings import (
            DEFAULT_TELEMETRY_API_URL,
            TelemetrySettings,
        )

        settings = TelemetrySettings.resolve(
            external_conf={"api_endpoint": "https://dashboard.example.test"}
        )
        self.assertEqual(settings.api_url, DEFAULT_TELEMETRY_API_URL)

    def test_empty_config_value_falls_back_to_disabled_not_default(self):
        """An empty ``telemetry_level =`` (or ``CODECARBON_TELEMETRY_LEVEL=``)
        must go through the invalid branch to disabled, not be treated as
        unset and silently resolve to the default ``minimal``.
        """
        from codecarbon.core.telemetry.schemas import TelemetryLevel
        from codecarbon.core.telemetry.settings import TelemetrySettings

        settings = TelemetrySettings.resolve(external_conf={"telemetry_level": ""})
        self.assertIs(settings.level, TelemetryLevel.disabled)
        self.assertTrue(settings.is_explicit)

    def test_privacy_intent_strings_fall_back_to_disabled_not_minimal(self):
        """off/false/none/0 must never resolve to a level that sends data."""
        from codecarbon.core.telemetry.schemas import TelemetryLevel
        from codecarbon.core.telemetry.settings import TelemetrySettings

        for value in ("off", "false", "none", "0"):
            with self.subTest(value=value):
                settings = TelemetrySettings.resolve(
                    external_conf={"telemetry_level": value}
                )
                self.assertIs(settings.level, TelemetryLevel.disabled)


if __name__ == "__main__":
    unittest.main()
