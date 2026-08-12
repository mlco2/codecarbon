import json
import xml.etree.ElementTree as ET

import pytest
from typer.testing import CliRunner

from codecarbon import badge
from codecarbon.cli.main import codecarbon as cli_app

CSV_CONTENT = """timestamp,project_name,emissions,energy_consumed
2024-01-01T00:00:00,alpha,0.001,0.010
2024-01-02T00:00:00,beta,0.500,1.000
2024-01-03T00:00:00,alpha,0.003,0.020
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


def test_render_svg_is_wellformed():
    svg = badge.render_svg("carbon", "12.4 gCO2eq/run")
    root = ET.fromstring(svg)
    texts = [element.text for element in root.iter("{http://www.w3.org/2000/svg}text")]
    assert "12.4 gCO2eq/run" in texts
    assert "carbon" in texts


def test_render_svg_escapes():
    assert "<script>" not in badge.render_svg("a<script>", "b & c")


def test_endpoint_json_schema():
    payload = json.loads(badge.render_endpoint_json("carbon", "12.4 gCO2eq"))
    assert payload == {
        "schemaVersion": 1,
        "label": "carbon",
        "message": "12.4 gCO2eq",
        "color": badge.DEFAULT_COLOR,
    }


def test_write_creates_both_files(emissions_file, tmp_path):
    paths = badge.write(emissions_file, output_dir=tmp_path / "assets")
    assert [path.name for path in paths] == [
        "codecarbon-badge.svg",
        "codecarbon-badge.json",
    ]
    assert all(path.is_file() for path in paths)


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
    assert (tmp_path / "codecarbon-badge.svg").is_file()
    assert (tmp_path / "codecarbon-badge.json").is_file()


def test_cli_badge_missing_file(tmp_path):
    result = CliRunner().invoke(
        cli_app, ["badge", "--file", str(tmp_path / "nope.csv")]
    )
    assert result.exit_code == 1
