"""Integration tests for telemetry tier resolution and config contract (Task 5)."""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from codecarbon.core.config import get_config_file_settings
from codecarbon.core.telemetry import (
    Telemetry,
    TelemetryLevel,
    TelemetrySettings,
    post_private,
)
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from tests.testutils import ensure_telemetry_run_duration, get_custom_mock_open

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")


def _conf(level: str) -> str:
    return f"[codecarbon]\ntelemetry_level = {level}\n"


class TestTelemetryConfigContract(unittest.TestCase):
    def setUp(self) -> None:
        Telemetry._default_warning_shown = False

    def tearDown(self) -> None:
        Telemetry._default_warning_shown = False

    def test_warns_once_when_telemetry_not_explicit(self):
        settings = TelemetrySettings.resolve(config_file_conf={})
        telemetry = Telemetry(settings)
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            telemetry.warn_if_implicit()
            telemetry.warn_if_implicit()
        self.assertEqual(mock_warning.call_count, 1)
        self.assertIn("Tier 1", mock_warning.call_args[0][0])

    def test_no_warn_when_config_explicit(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "disabled"}
        )
        telemetry = Telemetry(settings)
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            telemetry.warn_if_implicit()
        mock_warning.assert_not_called()

    def test_tier1_posts_to_telemetry_endpoint(self):
        tier1_payload = {
            "timestamp": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "telemetry_level": "minimal",
            "total_emissions_kg": 0.001,
            "os": "Linux",
        }
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_api_url": "http://tier1.example"}
        )
        with patch("codecarbon.core.telemetry.client.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = "telemetry-id"
            post_private(settings, tier1_payload)
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.kwargs["url"], "http://tier1.example/telemetry"
        )
        self.assertEqual(
            mock_post.call_args.kwargs["json"]["telemetry_level"],
            TelemetryLevel.minimal.value,
        )
        self.assertIn("total_emissions_kg", mock_post.call_args.kwargs["json"])

    def test_legacy_env_codecarbon_telemetry_does_not_change_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / ".codecarbon.config"
            local_path.write_text(_conf("minimal"))
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=("/nonexistent/global", str(local_path)),
            ):
                with patch.dict(
                    os.environ,
                    {"CODECARBON_TELEMETRY": "disabled"},
                    clear=False,
                ):
                    from codecarbon.core.config import get_hierarchical_config

                    settings = TelemetrySettings.resolve(
                        config_file_conf=get_config_file_settings(),
                        external_conf=get_hierarchical_config(),
                    )
        self.assertEqual(settings.level, TelemetryLevel.minimal)

    def test_env_codecarbon_telemetry_level_overrides_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / ".codecarbon.config"
            local_path.write_text(_conf("minimal"))
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=("/nonexistent/global", str(local_path)),
            ):
                with patch.dict(
                    os.environ,
                    {"CODECARBON_TELEMETRY_LEVEL": "disabled"},
                    clear=False,
                ):
                    from codecarbon.core.config import get_hierarchical_config

                    settings = TelemetrySettings.resolve(
                        config_file_conf=get_config_file_settings(),
                        external_conf=get_hierarchical_config(),
                    )
        self.assertEqual(settings.level, TelemetryLevel.disabled)

    def test_telemetry_api_url_env_used_for_tier2_client(self):
        with patch.dict(
            os.environ,
            {"CODECARBON_TELEMETRY_API_URL": "http://env-telemetry.example"},
            clear=False,
        ):
            settings = TelemetrySettings.resolve()
        self.assertEqual(settings.api_url, "http://env-telemetry.example")

    def test_telemetry_api_url_from_config_overrides_default(self):
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_api_url": "http://config-telemetry.example"}
        )
        self.assertEqual(settings.api_url, "http://config-telemetry.example")


@mock_platform_cli_setup
class TestTrackerTelemetryFromConfig(unittest.TestCase):
    def setUp(self) -> None:
        Telemetry._default_warning_shown = False
        self._config_patcher = None

    def tearDown(self) -> None:
        if self._config_patcher:
            self._config_patcher.stop()
        Telemetry._default_warning_shown = False

    def _mock_config(self, conf: str) -> None:
        self._config_patcher = patch(
            "builtins.open", new_callable=get_custom_mock_open(conf, conf)
        )
        self._config_patcher.start()

    def test_disabled_no_telemetry_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("disabled"))
        with patch("codecarbon.core.telemetry.dispatcher.post_private") as mock_post:
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                tracker = EmissionsTracker(
                    measure_power_secs=1,
                    save_to_api=False,
                    save_to_file=False,
                )
                tracker.start()
                tracker.stop()
        mock_post.assert_not_called()

    def test_minimal_posts_tier1_on_stop_not_on_init(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    tracker = EmissionsTracker(
                        measure_power_secs=1,
                        save_to_api=False,
                        save_to_file=False,
                    )
                    tracker.start()
                    tracker.stop()
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args[0][1]["telemetry_level"],
            TelemetryLevel.minimal.value,
        )

    def test_tier2_posts_tier1_and_emission_on_stop_not_on_init(self, mock_cli_setup):
        self._mock_config(_conf("extensive"))
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                with patch(
                    "codecarbon.core.telemetry.client.ApiClient"
                ) as mock_api_cls:
                    mock_api = MagicMock()
                    mock_api.add_emission.return_value = True
                    mock_api_cls.return_value = mock_api
                    with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                        tracker = EmissionsTracker(
                            measure_power_secs=1,
                            save_to_api=False,
                            save_to_file=False,
                        )
                        tracker.start()
                        tracker.stop()
        mock_post.assert_called_once()
        mock_api_cls.assert_called_once()
        mock_api.add_emission.assert_called_once()

    def test_offline_minimal_posts_tier1_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                tracker = OfflineEmissionsTracker(
                    country_iso_code="CAN",
                    save_to_api=False,
                    save_to_file=False,
                )
                tracker.start()
                tracker.stop()
        mock_post.assert_called_once()

    def test_warns_when_config_has_no_explicit_telemetry_level(self, mock_cli_setup):
        self._mock_config("[codecarbon]\n")
        env_without_telemetry = {
            key: value
            for key, value in os.environ.items()
            if key.lower()
            not in (
                "codecarbon_telemetry",
                "codecarbon_telemetry_level",
            )
        }
        with patch.dict(os.environ, env_without_telemetry, clear=True):
            with patch(
                "codecarbon.core.telemetry.dispatcher.logger.warning"
            ) as mock_warning:
                with patch(
                    "codecarbon.core.telemetry.dispatcher.post_private",
                    return_value=True,
                ):
                    with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                        EmissionsTracker(save_to_api=False, save_to_file=False)
        configure_warnings = [
            c
            for c in mock_warning.call_args_list
            if c[0] and "telemetry" in str(c[0][0]).lower()
        ]
        self.assertEqual(len(configure_warnings), 1)

    def test_no_configure_warn_when_telemetry_level_kwarg_set(self, mock_cli_setup):
        self._mock_config("[codecarbon]\n")
        with patch(
            "codecarbon.core.telemetry.dispatcher.logger.warning"
        ) as mock_warning:
            with patch("codecarbon.core.telemetry.dispatcher.post_private"):
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    EmissionsTracker(
                        telemetry_level="disabled",
                        save_to_api=False,
                        save_to_file=False,
                    )
        configure_warnings = [
            c for c in mock_warning.call_args_list if c[0] and "Tier 1" in str(c[0][0])
        ]
        self.assertEqual(len(configure_warnings), 0)

    def test_env_telemetry_disabled_does_not_change_resolved_level(
        self, mock_cli_setup
    ):
        self._mock_config(_conf("minimal"))
        with ensure_telemetry_run_duration():
            with patch.dict(
                os.environ, {"CODECARBON_TELEMETRY": "disabled"}, clear=False
            ):
                with patch(
                    "codecarbon.core.telemetry.dispatcher.post_private",
                    return_value=True,
                ) as mock_post:
                    with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                        tracker = EmissionsTracker(
                            save_to_api=False, save_to_file=False
                        )
                        tracker.start()
                        tracker.stop()
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
