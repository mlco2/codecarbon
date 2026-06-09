import configparser

import pytest

from codecarbon.cli import cli_utils


def test_get_config_reads_codecarbon_section(tmp_path):
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\napi_endpoint=https://example.test\n")

    config = cli_utils.get_config(config_path)

    assert config["api_endpoint"] == "https://example.test"


def test_get_config_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        cli_utils.get_config(tmp_path / ".codecarbon.config")


def test_get_api_endpoint_appends_default_when_missing_key(tmp_path):
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\n")

    endpoint = cli_utils.get_api_endpoint(config_path)

    assert endpoint == "https://api.codecarbon.io"
    parser = configparser.ConfigParser()
    parser.read(config_path)
    assert parser["codecarbon"]["api_endpoint"] == "https://api.codecarbon.io"


def test_get_api_endpoint_returns_default_when_file_missing(tmp_path):
    endpoint = cli_utils.get_api_endpoint(tmp_path / ".codecarbon.config")

    assert endpoint == "https://api.codecarbon.io"


def test_get_existing_exp_id_returns_none_on_key_error(monkeypatch):
    def raise_key_error():
        raise KeyError("missing")

    monkeypatch.setattr(cli_utils, "get_hierarchical_config", raise_key_error)

    assert cli_utils.get_existing_exp_id() is None


def test_get_existing_exp_id_reads_experiment_id(monkeypatch):
    monkeypatch.setattr(
        cli_utils, "get_hierarchical_config", lambda: {"experiment_id": "exp-123"}
    )

    assert cli_utils.get_existing_exp_id() == "exp-123"


def test_write_local_exp_id_creates_section(tmp_path):
    config_path = tmp_path / ".codecarbon.config"

    cli_utils.write_local_exp_id("exp-456", config_path)

    parser = configparser.ConfigParser()
    parser.read(config_path)
    assert parser["codecarbon"]["experiment_id"] == "exp-456"


def test_overwrite_local_config_updates_existing_file(tmp_path):
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\nexperiment_id=old\n")

    cli_utils.overwrite_local_config("experiment_id", "new", config_path)

    parser = configparser.ConfigParser()
    parser.read(config_path)
    assert parser["codecarbon"]["experiment_id"] == "new"


def test_create_new_config_file_creates_parent_and_file(monkeypatch, tmp_path):
    target = tmp_path / "nested" / ".codecarbon.config"
    prompts = iter([str(target)])

    monkeypatch.setattr(
        cli_utils.typer, "prompt", lambda *args, **kwargs: next(prompts)
    )
    monkeypatch.setattr(cli_utils.Confirm, "ask", lambda *args, **kwargs: True)

    created_path = cli_utils.create_new_config_file()

    assert created_path == target
    assert target.exists()
    assert target.read_text() == "[codecarbon]\n"


def test_create_new_config_file_expands_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    target = home / ".codecarbon.config"

    monkeypatch.setattr(cli_utils.Path, "home", lambda: home)
    monkeypatch.setattr(
        cli_utils.typer, "prompt", lambda *args, **kwargs: "~/.codecarbon.config"
    )

    created_path = cli_utils.create_new_config_file()

    assert created_path == target
    assert target.exists()
