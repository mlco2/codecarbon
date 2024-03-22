from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from codecarbon.cli.cli_utils import create_new_config_file


def test_create_new_config_file():
    runner = CliRunner()

    # Mock the typer.prompt function
    with patch("codecarbon.cli.cli_utils.typer.prompt") as mock_prompt:
        mock_prompt.return_value = "./.codecarbon.config"

        result = runner.invoke(create_new_config_file)

        assert result.exit_code == 0
        assert "Config file created at" in result.stdout

        # Verify that the prompt was called with the correct arguments
        mock_prompt.assert_called_once_with(
            "Where do you want to put your config file ?",
            type=str,
            default="./.codecarbon.config",
        )

        # Verify that the file was created
        file_path = Path("./.codecarbon.config")
        assert file_path.exists()
        assert file_path.is_file()
        assert file_path.read_text() == "[codecarbon]\n"
