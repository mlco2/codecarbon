import json

import pytest
from typer.testing import CliRunner

from codecarbon import badge
from codecarbon.cli.main import codecarbon as cli_app

CSV_CONTENT = """timestamp,project_name,run_id,emissions,energy_consumed
2024-01-01T00:00:00,alpha,run-1,0.001,0.010
2024-01-02T00:00:00,beta,run-2,0.500,1.000
2024-01-03T00:00:00,alpha,run-3,0.003,0.020
"""

# Two runs, flushed several times each. Every row holds the cumulative total of
# its run, so only the last row of each run counts.
MULTI_FLUSH_CSV = """timestamp,project_name,run_id,emissions,energy_consumed
2024-01-01T00:00:00,alpha,run-1,0.001,0.010
2024-01-01T00:01:00,alpha,run-1,0.002,0.020
2024-01-01T00:02:00,alpha,run-1,0.004,0.040
2024-01-02T00:00:00,alpha,run-2,0.005,0.050
2024-01-02T00:01:00,alpha,run-2,0.006,0.060
"""


@pytest.fixture
def emissions_file(tmp_path):
    path = tmp_path / "emissions.csv"
    path.write_text(CSV_CONTENT, encoding="utf-8")
    return path


def test_load_runs_filters_project(emissions_file):
    assert len(badge.load_runs(emissions_file)) == 3
    assert len(badge.load_runs(emissions_file, project="alpha")) == 2


def test_load_runs_errors_cleanly(tmp_path, emissions_file):
    with pytest.raises(FileNotFoundError):
        badge.load_runs(tmp_path / "nope.csv")
    with pytest.raises(ValueError):
        badge.load_runs(emissions_file, project="gamma")


def test_select_last_mean_total(emissions_file):
    rows = badge.load_runs(emissions_file, project="alpha")
    assert badge.summarise(rows, "last")["emissions"] == pytest.approx(0.003)
    assert badge.summarise(rows, "mean")["emissions"] == pytest.approx(0.002)
    assert badge.summarise(rows, "total")["emissions"] == pytest.approx(0.004)
    assert badge.summarise(rows, "total")["energy_consumed"] == pytest.approx(0.030)
    assert badge.summarise(rows, "last")["runs"] == 2
    with pytest.raises(ValueError):
        badge.summarise(rows, "median")


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        (0.0000004, "0.4 mgCO2eq"),
        (0.004, "4 gCO2eq"),
        (0.5, "500 gCO2eq"),
        (12.0, "12 kgCO2eq"),
        (12000.0, "12 MgCO2eq"),
    ],
)
def test_format_value_units(value, expected):
    assert badge.format_value(value) == expected


def test_message_for_metrics():
    summary = {"emissions": 0.0124, "energy_consumed": 0.031}
    assert badge.message_for(summary, "mean") == "12.4 gCO2eq/run"
    assert badge.message_for(summary, "total", "both") == "12.4 gCO2eq | 31 Wh total"


def test_cumulative_rows_are_not_double_counted(tmp_path):
    path = tmp_path / "emissions.csv"
    path.write_text(MULTI_FLUSH_CSV, encoding="utf-8")
    rows = badge.load_runs(path)
    assert badge.summarise(rows, "last")["emissions"] == pytest.approx(0.006)
    assert badge.summarise(rows, "total")["emissions"] == pytest.approx(0.010)
    assert badge.summarise(rows, "mean")["emissions"] == pytest.approx(0.005)
    assert badge.summarise(rows, "total")["energy_consumed"] == pytest.approx(0.100)
    assert badge.summarise(rows, "last")["runs"] == 2


def test_endpoint_json_quotes_are_escaped():
    payload = json.loads(badge.render_endpoint_json('a "quoted" label', "b & c"))
    assert payload["label"] == 'a "quoted" label'


def test_endpoint_json_schema():
    payload = json.loads(badge.render_endpoint_json("carbon", "12.4 gCO2eq"))
    assert payload == {
        "schemaVersion": 1,
        "label": "carbon",
        "message": "12.4 gCO2eq",
        "color": badge.DEFAULT_COLOR,
    }


def test_write_creates_endpoint_file(emissions_file, tmp_path):
    path = badge.write(emissions_file, output_dir=tmp_path / "assets")
    assert path.name == "codecarbon-badge.json"
    assert json.loads(path.read_text())["schemaVersion"] == 1


def test_cli_badge_writes_files(emissions_file, tmp_path):
    result = CliRunner().invoke(
        cli_app,
        [
            "badge",
            "--file",
            str(emissions_file),
            "--project",
            "alpha",
            "--select",
            "mean",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "codecarbon-badge.json").is_file()


def test_cli_badge_missing_file(tmp_path):
    result = CliRunner().invoke(
        cli_app, ["badge", "--file", str(tmp_path / "nope.csv")]
    )
    assert result.exit_code == 1
