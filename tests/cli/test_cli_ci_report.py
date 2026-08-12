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

# Captured verbatim from an `EmissionsTracker` run that flushed twice before
# stopping (measure_power_secs=1, ~12 s). Note that every row holds the
# *cumulative* totals since `start()`: duration goes 6.1 -> 9.1 -> 12.1 and the
# emissions of the last row are exactly what `stop()` returned. Do not replace
# this with hand-written per-flush deltas: CodeCarbon never writes those.
REAL_RUN_CSV = """timestamp,project_name,run_id,experiment_id,duration,emissions,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed,water_consumed,country_name,country_iso_code,region,cloud_provider,cloud_region,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,longitude,latitude,ram_total_size,tracking_mode,cpu_utilization_percent,gpu_utilization_percent,ram_utilization_percent,ram_used_gb,on_cloud,pue,wue
2026-08-12T19:37:29,realrun,3b540626-49b2-49c4-bd31-9adabd153544,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,6.111706958006835,4.3679212303523465e-06,7.146810637951176e-07,8.8272095485,0.0,6.0,1.4971799426185554e-05,0.0,1.0123984718326636e-05,2.5095784144512187e-05,0.0,Spain,ESP,madrid,,,macOS-26.5.2-arm64-arm-64bit-Mach-O,3.13.13,3.3.0,10,Apple M5,0,,-3.7011,40.4327,24.0,machine,0.0,0,64.23333333333333,9.161565144856771,N,1.0,0.0
2026-08-12T19:37:32,realrun,3b540626-49b2-49c4-bd31-9adabd153544,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,9.119719916001486,1.1022370326871737e-05,1.2086303557998372e-06,9.060489177045456,0.0,6.0,2.308286981475956e-05,0.0,1.515010402332943e-05,3.823297383808899e-05,0.0,Spain,ESP,madrid,,,macOS-26.5.2-arm64-arm-64bit-Mach-O,3.13.13,3.3.0,10,Apple M5,0,,-3.7011,40.4327,24.0,machine,11.11111111111111,0,64.46666666666667,9.215199788411459,N,1.0,0.0
2026-08-12T19:37:35,realrun,3b540626-49b2-49c4-bd31-9adabd153544,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,12.128133875005005,1.3327795140966287e-05,1.0989155692314441e-06,9.227810751732145,0.0,6.0,3.1311891250182006e-05,0.0,2.0166844231656195e-05,5.14787354818382e-05,0.0,Spain,ESP,madrid,,,macOS-26.5.2-arm64-arm-64bit-Mach-O,3.13.13,3.3.0,10,Apple M5,0,,-3.7011,40.4327,24.0,machine,8.333333333333334,0,64.60833333333333,9.254739125569662,N,1.0,0.0
"""


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

    def test_summarise_takes_the_totals_of_the_last_row_not_the_sum(self):
        """A real run's rows are cumulative, so summing them double-counts."""
        path = self.tmp_path / "emissions.csv"
        path.write_text(REAL_RUN_CSV)

        summary = summarise(path)
        self.assertEqual(summary.rows, 3)
        # The value `tracker.stop()` returned for this very run.
        self.assertAlmostEqual(summary.emissions, 1.3327795140966287e-05)
        self.assertAlmostEqual(summary.energy_consumed, 5.14787354818382e-05)
        self.assertAlmostEqual(summary.duration, 12.128133875005005)
        self.assertEqual(summary.project_name, "realrun")
        self.assertEqual(summary.country_iso_code, "ESP")
        self.assertEqual(summary.region, "madrid")

        # Summing the three flushes would report 2.9x the emissions and a 27 s
        # run instead of a 12 s one.
        self.assertLess(summary.emissions, 2e-05)
        self.assertLess(summary.duration, 13)

    def test_summarise_ignores_previous_runs(self):
        lines = REAL_RUN_CSV.splitlines(keepends=True)
        older = lines[1].replace("3b540626-49b2-49c4-bd31-9adabd153544", "older-run")
        path = self.tmp_path / "emissions.csv"
        path.write_text(lines[0] + older + "".join(lines[1:]))

        summary = summarise(path)
        self.assertEqual(summary.rows, 3)
        self.assertAlmostEqual(summary.emissions, 1.3327795140966287e-05)

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
