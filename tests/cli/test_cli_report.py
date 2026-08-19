"""Tests for the `codecarbon report` CLI command."""

import csv
import json
import os

import pytest
from typer.testing import CliRunner

from codecarbon.cli.main import codecarbon


runner = CliRunner()

SAMPLE_CSV_HEADERS = [
    "timestamp",
    "project_name",
    "run_id",
    "duration",
    "emissions",
    "emissions_rate",
    "cpu_power",
    "gpu_power",
    "ram_power",
    "cpu_energy",
    "gpu_energy",
    "ram_energy",
    "energy_consumed",
    "water_consumed",
    "country_name",
    "country_iso_code",
    "region",
    "cloud_provider",
    "cloud_region",
    "os",
    "python_version",
    "codecarbon_version",
    "cpu_count",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "longitude",
    "latitude",
    "ram_total_size",
    "tracking_mode",
]

SAMPLE_ROW_1 = [
    "2024-01-01T00:00:00",
    "project_alpha",
    "run-001",
    "120.5",
    "0.0015",
    "0.00001",
    "55.0",
    "120.0",
    "10.0",
    "0.001",
    "0.002",
    "0.0002",
    "0.0032",
    "0.02",
    "France",
    "FRA",
    "ile-de-france",
    "",
    "",
    "Linux",
    "3.11.0",
    "3.3.0",
    "8",
    "Intel i7",
    "1",
    "RTX 4090",
    "2.3522",
    "48.8566",
    "32.0",
    "machine",
]

SAMPLE_ROW_2 = [
    "2024-01-02T00:00:00",
    "project_beta",
    "run-002",
    "300.0",
    "0.005",
    "0.00002",
    "65.0",
    "200.0",
    "12.0",
    "0.003",
    "0.006",
    "0.0005",
    "0.0095",
    "0.05",
    "Germany",
    "DEU",
    "berlin",
    "",
    "",
    "Linux",
    "3.12.0",
    "3.3.0",
    "16",
    "AMD Ryzen 9",
    "2",
    "RTX 3090",
    "13.405",
    "52.52",
    "64.0",
    "machine",
]


def _write_sample_csv(path, rows=None):
    """Write a sample emissions CSV file for testing."""
    if rows is None:
        rows = [SAMPLE_ROW_1]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SAMPLE_CSV_HEADERS)
        for row in rows:
            writer.writerow(row)


class TestReportCommand:
    """Tests for `codecarbon report`."""

    def test_report_basic(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path)

        result = runner.invoke(codecarbon, ["report", "--file", str(csv_path)])
        assert result.exit_code == 0
        assert "Emissions Summary" in result.output

    def test_report_shows_equivalences(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path)

        result = runner.invoke(codecarbon, ["report", "--file", str(csv_path)])
        assert result.exit_code == 0
        assert "Equivalences" in result.output
        assert "Car travel" in result.output
        assert "Flights" in result.output
        assert "TV watching" in result.output

    def test_report_file_not_found(self, tmp_path):
        result = runner.invoke(
            codecarbon, ["report", "--file", str(tmp_path / "nonexistent.csv")]
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_report_empty_csv(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        # Write headers only, no data rows
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(SAMPLE_CSV_HEADERS)

        result = runner.invoke(codecarbon, ["report", "--file", str(csv_path)])
        assert result.exit_code == 0
        assert "no data" in result.output.lower() or "Warning" in result.output

    def test_report_json_format(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path)

        result = runner.invoke(
            codecarbon, ["report", "--file", str(csv_path), "--format", "json"]
        )
        assert result.exit_code == 0
        # Output should be valid JSON
        output_text = result.output.strip()
        parsed = json.loads(output_text)
        assert "summary" in parsed
        assert "equivalences" in parsed
        assert parsed["summary"]["num_runs"] == 1

    def test_report_json_has_equivalences(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path)

        result = runner.invoke(
            codecarbon, ["report", "--file", str(csv_path), "--format", "json"]
        )
        parsed = json.loads(result.output.strip())
        eq = parsed["equivalences"]
        assert "car_km" in eq
        assert "flights_paris_nyc" in eq
        assert "tv_hours" in eq
        assert "smartphone_charges" in eq
        assert eq["emissions_kg"] > 0

    def test_report_project_filter(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path, rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])

        result = runner.invoke(
            codecarbon,
            [
                "report",
                "--file",
                str(csv_path),
                "--project",
                "project_alpha",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed["summary"]["num_runs"] == 1

    def test_report_project_filter_not_found(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path)

        result = runner.invoke(
            codecarbon,
            [
                "report",
                "--file",
                str(csv_path),
                "--project",
                "nonexistent_project",
            ],
        )
        assert result.exit_code == 0
        assert "No data found" in result.output or "Warning" in result.output

    def test_report_multiple_projects_shows_breakdown(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path, rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])

        result = runner.invoke(codecarbon, ["report", "--file", str(csv_path)])
        assert result.exit_code == 0
        assert "Per-Project Breakdown" in result.output
        assert "project_alpha" in result.output
        assert "project_beta" in result.output

    def test_report_single_project_no_breakdown(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path, rows=[SAMPLE_ROW_1])

        result = runner.invoke(codecarbon, ["report", "--file", str(csv_path)])
        assert result.exit_code == 0
        # Single project should NOT show per-project breakdown
        assert "Per-Project Breakdown" not in result.output

    def test_report_summary_values(self, tmp_path):
        csv_path = tmp_path / "emissions.csv"
        _write_sample_csv(csv_path, rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])

        result = runner.invoke(
            codecarbon,
            ["report", "--file", str(csv_path), "--format", "json"],
        )
        parsed = json.loads(result.output.strip())
        summary = parsed["summary"]
        assert summary["num_runs"] == 2
        assert summary["num_projects"] == 2
        # Total emissions = 0.0015 + 0.005 = 0.0065
        assert abs(summary["total_emissions_kg"] - 0.0065) < 1e-6
        # Total duration = 120.5 + 300.0 = 420.5
        assert abs(summary["total_duration_s"] - 420.5) < 1e-6
