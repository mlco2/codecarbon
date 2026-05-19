import os
import unittest
from unittest.mock import patch

from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_API_URL,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
    get_telemetry_api_key,
    get_telemetry_api_url,
    get_telemetry_experiment_id,
    is_telemetry_level_explicit,
    parse_telemetry_level,
    resolve_telemetry_level,
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


class TestResolveTelemetryLevel(unittest.TestCase):
    def test_default_is_minimal_when_unset(self):
        level = resolve_telemetry_level({})
        self.assertEqual(level, TelemetryLevel.minimal)

    def test_telemetry_level_from_config_file(self):
        level = resolve_telemetry_level({"telemetry_level": "disabled"})
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_telemetry_level_extensive(self):
        level = resolve_telemetry_level({"telemetry_level": "extensive"})
        self.assertEqual(level, TelemetryLevel.extensive)

    def test_env_telemetry_key_ignored(self):
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY": "disabled"}, clear=False):
            level = resolve_telemetry_level({"telemetry": "extensive"})
        self.assertEqual(level, TelemetryLevel.minimal)

    def test_invalid_level_falls_back_to_minimal(self):
        with patch("codecarbon.core.telemetry_settings.logger.error") as mock_error:
            level = resolve_telemetry_level({"telemetry_level": "bogus"})
        self.assertEqual(level, TelemetryLevel.minimal)
        mock_error.assert_called_once()

    def test_override_kwarg_takes_precedence_over_config_file(self):
        level = resolve_telemetry_level(
            {"telemetry_level": "minimal"}, override="disabled"
        )
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_override_kwarg_takes_precedence_over_external_conf(self):
        level = resolve_telemetry_level(
            external_conf={"telemetry_level": "extensive"},
            override="disabled",
        )
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_external_conf_env_overrides_file_when_merged(self):
        level = resolve_telemetry_level(
            {"telemetry_level": "minimal"},
            external_conf={"telemetry_level": "disabled"},
        )
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_env_telemetry_level_via_external_conf(self):
        with patch.dict(
            os.environ, {"CODECARBON_TELEMETRY_LEVEL": "disabled"}, clear=False
        ):
            from codecarbon.core.config import get_hierarchical_config

            level = resolve_telemetry_level(external_conf=get_hierarchical_config())
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_is_explicit_with_config_file(self):
        self.assertTrue(is_telemetry_level_explicit({"telemetry_level": "minimal"}))

    def test_is_explicit_with_override(self):
        self.assertTrue(is_telemetry_level_explicit({}, override="disabled"))

    def test_is_explicit_with_env_telemetry_level(self):
        self.assertTrue(
            is_telemetry_level_explicit(
                {}, external_conf={"telemetry_level": "minimal"}
            )
        )

    def test_is_not_explicit_when_unset(self):
        self.assertFalse(is_telemetry_level_explicit({}))


class TestTelemetryApiSettings(unittest.TestCase):
    def test_get_telemetry_api_url_from_conf(self):
        url = get_telemetry_api_url({"telemetry_api_url": "http://test.example"})
        self.assertEqual(url, "http://test.example")

    def test_get_telemetry_api_url_default(self):
        env = {
            k: v for k, v in os.environ.items() if k != "CODECARBON_TELEMETRY_API_URL"
        }
        with patch.dict(os.environ, env, clear=True):
            url = get_telemetry_api_url({})
        self.assertEqual(url, DEFAULT_TELEMETRY_API_URL)

    def test_get_telemetry_api_url_env_fallback(self):
        with patch.dict(
            os.environ,
            {"CODECARBON_TELEMETRY_API_URL": "http://env.example"},
            clear=False,
        ):
            url = get_telemetry_api_url({})
        self.assertEqual(url, "http://env.example")

    def test_get_telemetry_api_key_from_conf(self):
        key = get_telemetry_api_key({"telemetry_api_key": "cpt_test"})
        self.assertEqual(key, "cpt_test")

    def test_get_telemetry_api_key_uses_public_default_when_unset(self):
        env = {
            k: v for k, v in os.environ.items() if k != "CODECARBON_TELEMETRY_API_KEY"
        }
        with patch.dict(os.environ, env, clear=True):
            key = get_telemetry_api_key({})
        self.assertEqual(key, DEFAULT_TELEMETRY_API_KEY)

    def test_get_telemetry_experiment_id_from_conf(self):
        experiment_id = get_telemetry_experiment_id(
            {"telemetry_experiment_id": "00000000-0000-0000-0000-000000000001"}
        )
        self.assertEqual(experiment_id, "00000000-0000-0000-0000-000000000001")

    def test_get_telemetry_experiment_id_uses_public_default_when_unset(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k != "CODECARBON_TELEMETRY_EXPERIMENT_ID"
        }
        with patch.dict(os.environ, env, clear=True):
            experiment_id = get_telemetry_experiment_id({})
        self.assertEqual(experiment_id, DEFAULT_TELEMETRY_EXPERIMENT_ID)


if __name__ == "__main__":
    unittest.main()
