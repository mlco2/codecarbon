import os
import unittest
from unittest.mock import patch

from codecarbon.core.telemetry import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_API_URL,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
    TelemetryLevel,
    TelemetrySettings,
    parse_telemetry_level,
)


class TestParseTelemetryLevel(unittest.TestCase):
    def test_parse_accepts_enum(self):
        self.assertEqual(
            parse_telemetry_level(TelemetryLevel.minimal), TelemetryLevel.minimal
        )

    def test_parse_normalizes_case(self):
        self.assertEqual(parse_telemetry_level("EXTENSIVE"), TelemetryLevel.extensive)

    def test_parse_rejects_invalid(self):
        with self.assertRaises(ValueError):
            parse_telemetry_level("bogus")


class TestTelemetrySettingsResolve(unittest.TestCase):
    def test_default_is_minimal_when_unset(self):
        settings = TelemetrySettings.resolve(config_file_conf={})
        self.assertEqual(settings.level, TelemetryLevel.minimal)
        self.assertEqual(settings.source, "default")

    def test_telemetry_level_from_config_file(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "disabled"}
        )
        self.assertEqual(settings.level, TelemetryLevel.disabled)
        self.assertEqual(settings.source, "file")

    def test_telemetry_level_extensive(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "extensive"}
        )
        self.assertEqual(settings.level, TelemetryLevel.extensive)

    def test_env_telemetry_key_ignored(self):
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY": "disabled"}, clear=False):
            settings = TelemetrySettings.resolve(
                config_file_conf={"telemetry": "extensive"}
            )
        self.assertEqual(settings.level, TelemetryLevel.minimal)

    def test_invalid_level_falls_back_to_minimal(self):
        with patch("codecarbon.core.telemetry.settings.logger.error") as mock_error:
            settings = TelemetrySettings.resolve(
                config_file_conf={"telemetry_level": "bogus"}
            )
        self.assertEqual(settings.level, TelemetryLevel.minimal)
        mock_error.assert_called_once()

    def test_override_kwarg_takes_precedence_over_config_file(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "minimal"},
            override="disabled",
        )
        self.assertEqual(settings.level, TelemetryLevel.disabled)

    def test_override_kwarg_takes_precedence_over_external_conf(self):
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_level": "extensive"},
            override="disabled",
        )
        self.assertEqual(settings.level, TelemetryLevel.disabled)

    def test_external_conf_env_overrides_file_when_merged(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "minimal"},
            external_conf={"telemetry_level": "disabled"},
        )
        self.assertEqual(settings.level, TelemetryLevel.disabled)

    def test_env_telemetry_level_via_external_conf(self):
        with patch.dict(
            os.environ, {"CODECARBON_TELEMETRY_LEVEL": "disabled"}, clear=False
        ):
            from codecarbon.core.config import get_hierarchical_config

            settings = TelemetrySettings.resolve(
                external_conf=get_hierarchical_config()
            )
        self.assertEqual(settings.level, TelemetryLevel.disabled)

    def test_is_explicit_with_config_file(self):
        settings = TelemetrySettings.resolve(
            config_file_conf={"telemetry_level": "minimal"}
        )
        self.assertTrue(settings.is_explicit)

    def test_is_explicit_with_override(self):
        settings = TelemetrySettings.resolve(override="disabled")
        self.assertTrue(settings.is_explicit)

    def test_is_explicit_with_env_telemetry_level(self):
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_level": "minimal"}
        )
        self.assertTrue(settings.is_explicit)

    def test_is_not_explicit_when_unset(self):
        settings = TelemetrySettings.resolve(config_file_conf={})
        self.assertFalse(settings.is_explicit)


class TestTelemetryApiSettings(unittest.TestCase):
    def test_api_url_from_conf(self):
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_api_url": "http://test.example"}
        )
        self.assertEqual(settings.api_url, "http://test.example")

    def test_api_url_default(self):
        env = {
            k: v for k, v in os.environ.items() if k != "CODECARBON_TELEMETRY_API_URL"
        }
        with patch.dict(os.environ, env, clear=True):
            settings = TelemetrySettings.resolve()
        self.assertEqual(settings.api_url, DEFAULT_TELEMETRY_API_URL)

    def test_api_url_env_fallback(self):
        with patch.dict(
            os.environ,
            {"CODECARBON_TELEMETRY_API_URL": "http://env.example"},
            clear=False,
        ):
            settings = TelemetrySettings.resolve()
        self.assertEqual(settings.api_url, "http://env.example")

    def test_api_key_from_conf(self):
        settings = TelemetrySettings.resolve(
            external_conf={"telemetry_api_key": "cpt_test"}
        )
        self.assertEqual(settings.api_key, "cpt_test")

    def test_api_key_uses_public_default_when_unset(self):
        env = {
            k: v for k, v in os.environ.items() if k != "CODECARBON_TELEMETRY_API_KEY"
        }
        with patch.dict(os.environ, env, clear=True):
            settings = TelemetrySettings.resolve()
        self.assertEqual(settings.api_key, DEFAULT_TELEMETRY_API_KEY)

    def test_experiment_id_from_conf(self):
        settings = TelemetrySettings.resolve(
            external_conf={
                "telemetry_experiment_id": "00000000-0000-0000-0000-000000000001"
            }
        )
        self.assertEqual(settings.experiment_id, "00000000-0000-0000-0000-000000000001")

    def test_experiment_id_uses_public_default_when_unset(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k != "CODECARBON_TELEMETRY_EXPERIMENT_ID"
        }
        with patch.dict(os.environ, env, clear=True):
            settings = TelemetrySettings.resolve()
        self.assertEqual(settings.experiment_id, DEFAULT_TELEMETRY_EXPERIMENT_ID)


if __name__ == "__main__":
    unittest.main()
