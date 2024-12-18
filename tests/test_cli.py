import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from codecarbon import __app_name__, __version__
from codecarbon.cli.main import codecarbon

# MOCK API CLIENT


@patch("codecarbon.cli.main.ApiClient")
class TestApp(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_api_client = MagicMock()
        self.mock_api_client.get_list_organizations.return_value = [
            {"id": "1", "name": "test org Code Carbon"}
        ]
        self.mock_api_client.list_teams_from_organization.return_value = [
            {"id": "1", "name": "test team Code Carbon"}
        ]

        self.mock_api_client.list_projects_from_team.return_value = [
            {"id": "1", "name": "test project Code Carbon"}
        ]
        self.mock_api_client.list_experiments_from_project.return_value = [
            {"id": "1", "name": "test experiment Code Carbon"}
        ]
        self.mock_api_client.create_organization.return_value = {
            "id": "1",
            "name": "test org Code Carbon",
        }
        self.mock_api_client.create_team.return_value = {
            "id": "1",
            "name": "test team Code Carbon",
        }
        self.mock_api_client.create_project.return_value = {
            "id": "1",
            "name": "test project Code Carbon",
        }
        self.mock_api_client.add_experiment.return_value = {
            "id": "1",
            "name": "test experiment Code Carbon",
        }

    def test_app(self, MockApiClient):
        result = self.runner.invoke(codecarbon, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__app_name__, result.stdout)
        self.assertIn(__version__, result.stdout)

    @patch("codecarbon.cli.main.Path.exists")
    @patch("codecarbon.cli.main.Confirm.ask")
    @patch("codecarbon.cli.main.questionary_prompt")
    @patch("codecarbon.cli.main._get_access_token")
    def test_config_no_local_new_all(
        self, mock_token, mock_prompt, mock_confirm, mock_path_exists, MockApiClient
    ):
        temp_dir = os.getenv("RUNNER_TEMP", tempfile.gettempdir())
        temp_codecarbon_config = tempfile.NamedTemporaryFile(
            mode="w+t", delete=False, dir=temp_dir
        )

        def side_effect_wrapper(*args, **kwargs):
            """Side effect wrapper to simulate the first call to path.exists to avoid picking up global config"""
            if side_effect_wrapper.call_count == 0:
                side_effect_wrapper.call_count += 1
                return False
            else:
                return True

        side_effect_wrapper.call_count = 0
        mock_path_exists.side_effect = side_effect_wrapper
        MockApiClient.return_value = self.mock_api_client
        mock_token.return_value = "user_token"
        mock_prompt.side_effect = [
            "Create New Organization",
            "Create New Project",
            "Create New Experiment",
        ]
        mock_confirm.side_effect = [True, False, False, False]

        result = self.runner.invoke(
            codecarbon,
            ["config"],
            input=f"{temp_codecarbon_config.name}\n",
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Creating new experiment\nExperiment name : [Code Carbon user test]",
            result.stdout,
        )
        self.assertIn(
            "Consult configuration documentation for more configuration options",
            result.stdout,
        )

    @patch("codecarbon.cli.main._get_access_token")
    @patch("codecarbon.cli.main.Path.exists")
    @patch("codecarbon.cli.main.get_config")
    @patch("codecarbon.cli.main.questionary_prompt")
    def test_init_use_local(
        self, mock_prompt, mock_config, mock_path_exists, mock_token, MockApiClient
    ):
        mock_prompt.return_value = "~/.codecarbon.config"
        mock_config.return_value = {
            "api_endpoint": "http://localhost:8008",
            "organization_id": "114",
            "project_id": "133",
            "experiment_id": "yolo123",
        }
        mock_token.return_value = "mock_token"

        def side_effect_wrapper(*args, **kwargs):
            """Side effect wrapper to simulate the first call to path.exists to avoid picking up global config"""
            if side_effect_wrapper.call_count == 1:
                side_effect_wrapper.call_count += 1
                return False
            else:
                side_effect_wrapper.call_count += 1
                return True

        side_effect_wrapper.call_count = 0
        mock_path_exists.side_effects = side_effect_wrapper
        result = self.runner.invoke(codecarbon, ["config"], input="n")
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Using already existing global config file ",
            result.stdout,
        )

    def custom_questionary_side_effect(*args, **kwargs):
        default_value = kwargs.get("default")
        return MagicMock(return_value=default_value)


if __name__ == "__main__":
    unittest.main()
