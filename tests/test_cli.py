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
        self.mock_api_client.create_experiment.return_value = {
            "id": "1",
            "name": "test experiment Code Carbon",
        }

    def test_app(self, MockApiClient):
        result = self.runner.invoke(codecarbon, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__app_name__, result.stdout)
        self.assertIn(__version__, result.stdout)

    def test_init_aborted(self, MockApiClient):
        result = self.runner.invoke(codecarbon, ["config", "--init"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Welcome to CodeCarbon configuration wizard", result.stdout)

    @patch("codecarbon.cli.main.questionary_prompt")
    def test_init_use_local(self, mock_prompt, MockApiClient):
        mock_prompt.return_value = "/.codecarbonconfig"
        result = self.runner.invoke(codecarbon, ["config", "--init"], input="y")
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Succesfully initiated Code Carbon ! \n Here is your detailed config : \n ",
            result.stdout,
        )

    def custom_questionary_side_effect(*args, **kwargs):
        default_value = kwargs.get("default")
        return MagicMock(return_value=default_value)

    @patch("codecarbon.cli.main.Confirm.ask")
    @patch("codecarbon.cli.main.questionary_prompt")
    def test_init_no_local_new_all(self, mock_prompt, mock_confirm, MockApiClient):
        MockApiClient.return_value = self.mock_api_client
        mock_prompt.side_effect = [
            "Create New Config",
            "Create New Organization",
            "Create New Team",
            "Create New Project",
            "Create New Experiment",
        ]
        mock_confirm.side_effect = [False, False, False]
        result = self.runner.invoke(
            codecarbon,
            ["config", "--init"],
            input="y",
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Succesfully initiated Code Carbon ! \n Here is your detailed config : \n ",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
