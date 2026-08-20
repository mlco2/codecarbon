import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codecarbon.core.config import get_config_file_settings, get_hierarchical_config


class TestGetConfigFileSettings(unittest.TestCase):
    def test_returns_empty_when_no_config_files(self):
        with patch("codecarbon.core.config._config_file_paths") as mock_paths:
            mock_paths.return_value = ("/nonexistent/global", "/nonexistent/local")
            settings = get_config_file_settings()
        self.assertEqual(settings, {})

    def test_local_overrides_global_telemetry_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            global_path = Path(tmp) / "global.config"
            local_path = Path(tmp) / "local.config"
            global_path.write_text("[codecarbon]\ntelemetry_level = minimal\n")
            local_path.write_text("[codecarbon]\ntelemetry_level = disabled\n")
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=(str(global_path), str(local_path)),
            ):
                settings = get_config_file_settings()
        self.assertEqual(settings["telemetry_level"], "disabled")

    def test_hierarchical_config_includes_env_but_file_settings_do_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / ".codecarbon.config"
            local_path.write_text("[codecarbon]\ntelemetry_level = minimal\n")
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=("/nonexistent/global", str(local_path)),
            ):
                with patch.dict(
                    os.environ,
                    {"CODECARBON_TELEMETRY": "disabled"},
                    clear=False,
                ):
                    file_settings = get_config_file_settings()
                    hierarchical = get_hierarchical_config()
        self.assertEqual(file_settings.get("telemetry_level"), "minimal")
        self.assertNotIn("telemetry", file_settings)
        self.assertEqual(hierarchical.get("telemetry"), "disabled")


if __name__ == "__main__":
    unittest.main()
