import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from codecarbon.cli.ci_report import (
    CIReportError,
    render,
    render_markdown,
    summarise,
)
from codecarbon.cli.main import codecarbon

HEADER = "timestamp,project_name,run_id,duration,emissions,energy_consumed,country_iso_code,region\n"


def write_csv(directory: Path, name: str, rows: str, header: str = HEADER) -> Path:
    path = directory / name
    path.write_text(header + rows)
    return path


class TestCIReport(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_summarise_sums_the_rows_of_the_last_run(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,old,run-1,10,0.5,1.0,FRA,IDF\n"
            "2024-01-02T00:00:00,proj,run-2,10,0.001,0.01,FRA,IDF\n"
            "2024-01-02T00:00:10,proj,run-2,5,0.002,0.02,FRA,IDF\n",
        )
        summary = summarise(csv_path)
        self.assertEqual(summary.rows, 2)
        self.assertAlmostEqual(summary.emissions, 0.003)
        self.assertAlmostEqual(summary.energy_consumed, 0.03)
        self.assertAlmostEqual(summary.duration, 15)
        self.assertEqual(summary.project_name, "proj")
        self.assertEqual(summary.country_iso_code, "FRA")

    def test_summarise_missing_file(self):
        with self.assertRaises(CIReportError):
            summarise(self.tmp_path / "nope.csv")

    def test_summarise_empty_file(self):
        with self.assertRaises(CIReportError):
            summarise(write_csv(self.tmp_path, "empty.csv", ""))

    def test_summarise_wrong_file(self):
        with self.assertRaises(CIReportError):
            summarise(
                write_csv(self.tmp_path, "other.csv", "1,2\n", header="foo,bar\n")
            )

    def test_summarise_ignores_unparseable_values(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,proj,run-1,10,,0.01,FRA,IDF\n",
        )
        self.assertEqual(summarise(csv_path).emissions, 0.0)

    def test_markdown_without_baseline_has_no_comparison(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,proj,run-1,94,0.0124,0.031,FRA,IDF\n",
        )
        report = render_markdown(summarise(csv_path), None, "pytest -q")
        self.assertIn("12.4 g CO2eq", report)
        self.assertIn("`pytest -q`", report)
        self.assertNotIn("vs baseline", report)

    def test_markdown_delta(self):
        current = summarise(
            write_csv(
                self.tmp_path,
                "emissions.csv",
                "2024-01-01T00:00:00,proj,run-2,94,0.0124,0.031,FRA,IDF\n",
            )
        )
        for baseline_emissions, expected in (
            (0.0105, "+1.9 g (+18%)"),
            (0.0143, "-1.9 g (-13%)"),
            (0.0124, "+0.0 g (+0%)"),
        ):
            baseline = summarise(
                write_csv(
                    self.tmp_path,
                    "baseline.csv",
                    f"2024-01-01T00:00:00,proj,run-1,90,{baseline_emissions},0.03,FRA,IDF\n",
                )
            )
            self.assertIn(expected, render_markdown(current, baseline))

    def test_markdown_delta_with_zero_baseline(self):
        current = summarise(
            write_csv(
                self.tmp_path,
                "emissions.csv",
                "2024-01-01T00:00:00,proj,run-2,94,0.0124,0.031,FRA,IDF\n",
            )
        )
        baseline = summarise(
            write_csv(
                self.tmp_path,
                "baseline.csv",
                "2024-01-01T00:00:00,proj,run-1,90,0,0,FRA,IDF\n",
            )
        )
        self.assertIn("+12.4 g", render_markdown(current, baseline))

    def test_unknown_format(self):
        summary = summarise(
            write_csv(
                self.tmp_path,
                "emissions.csv",
                "2024-01-01T00:00:00,proj,run-1,94,0.0124,0.031,FRA,IDF\n",
            )
        )
        with self.assertRaises(CIReportError):
            render(summary, output_format="xml")

    def test_cli_json_output(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,proj,run-1,94,0.0124,0.031,FRA,IDF\n",
        )
        baseline_path = write_csv(
            self.tmp_path,
            "baseline.csv",
            "2024-01-01T00:00:00,proj,run-0,90,0.0105,0.030,FRA,IDF\n",
        )
        result = self.runner.invoke(
            codecarbon,
            [
                "ci-report",
                "--csv",
                str(csv_path),
                "--baseline",
                str(baseline_path),
                "--format",
                "json",
                "--label",
                "pytest",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["label"], "pytest")
        self.assertAlmostEqual(payload["emissions_kg"], 0.0124)
        self.assertAlmostEqual(payload["energy_kwh"], 0.031)
        self.assertAlmostEqual(payload["delta_kg"], 0.0019)

    def test_cli_missing_baseline_is_not_an_error(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,proj,run-1,94,0.0124,0.031,FRA,IDF\n",
        )
        result = self.runner.invoke(
            codecarbon,
            [
                "ci-report",
                "--csv",
                str(csv_path),
                "--baseline",
                str(self.tmp_path / "nope.csv"),
                "--format",
                "json",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(json.loads(result.stdout)["delta_kg"])

    def test_cli_threshold(self):
        csv_path = write_csv(
            self.tmp_path,
            "emissions.csv",
            "2024-01-01T00:00:00,proj,run-1,94,0.0124,0.031,FRA,IDF\n",
        )
        for threshold, exit_code in (("0.05", 0), ("0.001", 1)):
            result = self.runner.invoke(
                codecarbon,
                ["ci-report", "--csv", str(csv_path), "--threshold-kg", threshold],
            )
            self.assertEqual(result.exit_code, exit_code)

    def test_cli_bad_csv_exits_cleanly(self):
        result = self.runner.invoke(
            codecarbon, ["ci-report", "--csv", str(self.tmp_path / "nope.csv")]
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No emissions file found", result.stdout)


if __name__ == "__main__":
    unittest.main()
