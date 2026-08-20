"""Test suite for the SCI (ISO/IEC 21031) output method."""

import json
import os
import shutil
import tempfile
import unittest

from codecarbon.emissions_tracker import BaseEmissionsTracker
from codecarbon.output_methods.base_output import OutputMethod
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData
from codecarbon.output_methods.sci import (
    SCI_SPEC_VERSION,
    EmbodiedDeclaration,
    FunctionalUnit,
    SCIOutput,
    map_emissions_to_sci,
)


def _make_emissions_data(**overrides) -> EmissionsData:
    """Create a realistic EmissionsData instance for testing."""
    defaults = dict(
        timestamp="2025-01-15T10:30:00",
        project_name="test_project",
        run_id="550e8400-e29b-41d4-a716-446655440000",
        experiment_id="exp-001",
        duration=3600.0,
        emissions=0.042,
        emissions_rate=1.17e-05,
        cpu_power=12.5,
        gpu_power=85.0,
        ram_power=3.2,
        cpu_energy=0.0125,
        gpu_energy=0.085,
        ram_energy=0.0032,
        energy_consumed=0.1007,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="ile-de-france",
        cloud_provider="",
        cloud_region="",
        os="Linux",
        python_version="3.11.0",
        codecarbon_version="3.0.0",
        cpu_count=8,
        cpu_model="Intel Xeon",
        gpu_count=1,
        gpu_model="NVIDIA A100",
        longitude=2.35,
        latitude=48.85,
        ram_total_size=64.0,
        tracking_mode="machine",
    )
    defaults.update(overrides)
    return EmissionsData(**defaults)


def _make_task_data(task_name: str, **overrides) -> TaskEmissionsData:
    data = _make_emissions_data(**overrides).values
    data.pop("experiment_id")
    data.pop("pue")
    data.pop("wue")
    return TaskEmissionsData(task_name=task_name, **data)


class TestSCIMapping(unittest.TestCase):
    """Mapping and arithmetic."""

    def test_sci_formula(self):
        data = _make_emissions_data()
        report = map_emissions_to_sci(
            data,
            functional_unit=FunctionalUnit(name="inference request", count=10_000),
            embodied=EmbodiedDeclaration(gco2e=42.5, source="vendor LCA"),
        )
        expected_i = data.emissions * 1000 / data.energy_consumed
        expected_sci = (data.energy_consumed * expected_i + 42.5) / 10_000

        self.assertAlmostEqual(report["sci"], expected_sci)
        self.assertAlmostEqual(report["terms"]["I_gCO2e_per_kWh"], expected_i)
        self.assertEqual(report["terms"]["E_kWh"], data.energy_consumed)
        self.assertEqual(report["terms"]["M_gCO2e"], 42.5)
        self.assertEqual(report["terms"]["R"], 10_000)
        self.assertEqual(report["unit"], "gCO2eq per inference request")
        self.assertEqual(report["specVersion"], SCI_SPEC_VERSION)
        self.assertEqual(report["provenance"]["M_source"], "vendor LCA")
        self.assertIn("FRA", report["provenance"]["I_source"])

    def test_provenance_fields(self):
        report = map_emissions_to_sci(
            _make_emissions_data(),
            functional_unit=FunctionalUnit(name="request", count=1),
            reporter={"organization": "Acme"},
            boundary="Application only.",
        )
        provenance = report["provenance"]
        self.assertEqual(provenance["hardware"]["cpu"], "Intel Xeon")
        self.assertEqual(provenance["hardware"]["gpu"], "NVIDIA A100")
        self.assertEqual(provenance["hardware"]["ramTotalGB"], 64.0)
        self.assertEqual(provenance["durationSeconds"], 3600.0)
        self.assertEqual(provenance["measurementBoundary"], "Application only.")
        self.assertEqual(report["reporter"], {"organization": "Acme"})


class TestUndeclaredTerms(unittest.TestCase):
    """Undeclared terms."""

    def test_no_functional_unit(self):
        report = map_emissions_to_sci(_make_emissions_data())
        self.assertIsNone(report["sci"])
        self.assertIn("status", report)
        self.assertIn("functional unit", report["status"])

    def test_zero_functional_unit_count(self):
        report = map_emissions_to_sci(
            _make_emissions_data(), functional_unit=FunctionalUnit(name="req", count=0)
        )
        self.assertIsNone(report["sci"])
        self.assertIn("status", report)

    def test_embodied_not_declared(self):
        report = map_emissions_to_sci(
            _make_emissions_data(),
            functional_unit=FunctionalUnit(name="req", count=10),
        )
        self.assertEqual(report["terms"]["M_gCO2e"], 0.0)
        self.assertEqual(report["provenance"]["M_source"], "not declared")

    def test_zero_energy_does_not_raise(self):
        report = map_emissions_to_sci(
            _make_emissions_data(energy_consumed=0.0, emissions=0.0),
            functional_unit=FunctionalUnit(name="req", count=10),
        )
        self.assertEqual(report["terms"]["I_gCO2e_per_kWh"], 0.0)
        self.assertEqual(report["sci"], 0.0)


class TestSCIOutput(unittest.TestCase):
    """Output handler."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_out_writes_report(self):
        data = _make_emissions_data()
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
        )
        handler.out(data, data)

        file_path = os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path) as f:
            report = json.load(f)
        self.assertIsNotNone(report["sci"])

    def test_set_functional_unit_count(self):
        data = _make_emissions_data()
        handler = SCIOutput(output_dir=self.temp_dir)
        handler.set_functional_unit_count(500, name="request")
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertEqual(report["terms"]["R"], 500)
        self.assertEqual(report["terms"]["R_name"], "request")

    def test_task_out_writes_one_entry_per_task(self):
        tasks = [_make_task_data("train"), _make_task_data("infer")]
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
        )
        handler.task_out(tasks, "experiment")

        file_path = os.path.join(
            self.temp_dir, f"sci_report_tasks_{tasks[0].run_id}.json"
        )
        with open(file_path) as f:
            report = json.load(f)
        self.assertEqual([t["taskName"] for t in report["tasks"]], ["train", "infer"])

    def test_set_functional_unit_count_updates_existing_unit(self):
        data = _make_emissions_data()
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=1),
        )
        handler.set_functional_unit_count(750)
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertEqual(report["terms"]["R"], 750)
        # name is kept when not given again
        self.assertEqual(report["terms"]["R_name"], "request")
        self.assertAlmostEqual(report["sci"], data.emissions * 1000 / 750, places=10)

    def test_set_functional_unit_count_renames_existing_unit(self):
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=1),
        )
        handler.set_functional_unit_count(10, name="image")
        data = _make_emissions_data()
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertEqual(report["terms"]["R_name"], "image")
        self.assertEqual(report["unit"], "gCO2eq per image")

    def test_out_logs_and_swallows_errors(self):
        handler = SCIOutput(output_dir=self.temp_dir)
        with self.assertLogs("codecarbon", level="ERROR") as logs:
            handler.out(object(), object())
        self.assertTrue(any("Failed to write SCI report" in m for m in logs.output))
        self.assertEqual(os.listdir(self.temp_dir), [])

    def test_task_out_without_tasks_writes_nothing(self):
        SCIOutput(output_dir=self.temp_dir).task_out([], "experiment")
        self.assertEqual(os.listdir(self.temp_dir), [])

    def test_task_out_logs_and_swallows_errors(self):
        handler = SCIOutput(output_dir=self.temp_dir)
        with self.assertLogs("codecarbon", level="ERROR") as logs:
            handler.task_out([object()], "experiment")
        self.assertTrue(
            any("Failed to write SCI task report" in m for m in logs.output)
        )
        self.assertEqual(os.listdir(self.temp_dir), [])

    def test_task_out_reports_sci_share_per_task(self):
        tasks = [
            _make_task_data("train", emissions=0.2, energy_consumed=0.5),
            _make_task_data("infer", emissions=0.1, energy_consumed=0.5),
        ]
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
            embodied=EmbodiedDeclaration(gco2e=10.0, source="vendor LCA"),
        )
        handler.task_out(tasks, "experiment")

        with open(
            os.path.join(self.temp_dir, f"sci_report_tasks_{tasks[0].run_id}.json")
        ) as f:
            report = json.load(f)
        self.assertEqual(report["experimentName"], "experiment")
        # equal durations, so each task carries half of the declared M
        self.assertAlmostEqual(report["tasks"][0]["sciShare"], (0.2 * 1000 + 5.0) / 100)
        self.assertAlmostEqual(report["tasks"][1]["sciShare"], (0.1 * 1000 + 5.0) / 100)
        # R is not apportioned, so no per-functional-unit label is claimed
        self.assertNotIn("unit", report["tasks"][0])
        self.assertIn("vendor LCA", report["tasks"][0]["provenance"]["M_source"])
        self.assertIn(
            "apportioned by duration", report["tasks"][0]["provenance"]["M_source"]
        )

    def test_task_out_apportions_embodied_by_duration(self):
        # The whole point: M is the device's embodied carbon for the whole run.
        # Handing every task the full M would report it once per task.
        tasks = [
            _make_task_data("short", duration=100.0),
            _make_task_data("long", duration=300.0),
        ]
        handler = SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
            embodied=EmbodiedDeclaration(gco2e=40.0, source="vendor LCA"),
        )
        handler.task_out(tasks, "experiment")

        with open(
            os.path.join(self.temp_dir, f"sci_report_tasks_{tasks[0].run_id}.json")
        ) as f:
            report = json.load(f)
        shares = [t["terms"]["M_gCO2e"] for t in report["tasks"]]
        self.assertAlmostEqual(shares[0], 10.0)
        self.assertAlmostEqual(shares[1], 30.0)
        # the split is exhaustive: the run's M is counted exactly once
        self.assertAlmostEqual(sum(shares), 40.0)
        self.assertIn("25.0% of the run", report["tasks"][0]["provenance"]["M_source"])

    def test_task_out_without_embodied_stays_undeclared(self):
        tasks = [_make_task_data("train")]
        SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
        ).task_out(tasks, "experiment")

        with open(
            os.path.join(self.temp_dir, f"sci_report_tasks_{tasks[0].run_id}.json")
        ) as f:
            report = json.load(f)
        self.assertEqual(report["tasks"][0]["terms"]["M_gCO2e"], 0.0)
        self.assertEqual(report["tasks"][0]["provenance"]["M_source"], "not declared")

    def test_task_out_with_zero_duration_does_not_divide_by_zero(self):
        tasks = [_make_task_data("instant", duration=0.0)]
        SCIOutput(
            output_dir=self.temp_dir,
            functional_unit=FunctionalUnit(name="request", count=100),
            embodied=EmbodiedDeclaration(gco2e=40.0, source="vendor LCA"),
        ).task_out(tasks, "experiment")

        with open(
            os.path.join(self.temp_dir, f"sci_report_tasks_{tasks[0].run_id}.json")
        ) as f:
            report = json.load(f)
        self.assertEqual(report["tasks"][0]["terms"]["M_gCO2e"], 0.0)

    def test_live_out_is_noop(self):
        data = _make_emissions_data()
        SCIOutput(output_dir=self.temp_dir).live_out(data, data)
        self.assertEqual(os.listdir(self.temp_dir), [])

    def test_output_method_enum(self):
        self.assertEqual(OutputMethod.SCI.value, "sci")


class TestContextFile(unittest.TestCase):
    """Context file loading."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_context(self, content: str) -> str:
        path = os.path.join(self.temp_dir, "sci_context.json")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_from_file(self):
        path = self._write_context(
            json.dumps(
                {
                    "functionalUnit": {"name": "inference request", "count": 10000},
                    "embodied": {"gCO2e": 42.5, "source": "manufacturer LCA"},
                    "reporter": {"organization": "Acme"},
                    "boundary": "Application only.",
                }
            )
        )
        handler = SCIOutput.from_file(path, output_dir=self.temp_dir)
        data = _make_emissions_data()
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertEqual(report["terms"]["R"], 10000)
        self.assertEqual(report["terms"]["M_gCO2e"], 42.5)
        self.assertEqual(report["provenance"]["M_source"], "manufacturer LCA")
        self.assertEqual(report["reporter"], {"organization": "Acme"})

    def test_from_file_empty_context_declares_nothing(self):
        path = self._write_context("{}")
        handler = SCIOutput.from_file(path, output_dir=self.temp_dir)
        data = _make_emissions_data()
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertIsNone(report["sci"])
        self.assertIsNone(report["terms"]["R_name"])
        self.assertEqual(report["terms"]["M_gCO2e"], 0.0)
        self.assertNotIn("reporter", report)

    def test_from_file_partial_declarations_use_defaults(self):
        path = self._write_context(
            json.dumps({"functionalUnit": {"count": 4}, "embodied": {"gco2e": 8.0}})
        )
        handler = SCIOutput.from_file(path, output_dir=self.temp_dir)
        data = _make_emissions_data()
        handler.out(data, data)

        with open(os.path.join(self.temp_dir, f"sci_report_{data.run_id}.json")) as f:
            report = json.load(f)
        self.assertEqual(report["terms"]["R"], 4)
        self.assertEqual(report["terms"]["R_name"], "")
        self.assertEqual(report["unit"], "gCO2eq per functional unit")
        self.assertEqual(report["provenance"]["M_source"], "not declared")
        self.assertAlmostEqual(report["sci"], (data.emissions * 1000 + 8.0) / 4)

    def test_from_file_accepts_both_embodied_spellings(self):
        for key in ("gCO2e", "gco2e"):
            path = self._write_context(
                json.dumps({"functionalUnit": {"count": 4}, "embodied": {key: 8.0}})
            )
            handler = SCIOutput.from_file(path, output_dir=self.temp_dir)
            self.assertEqual(handler._embodied.gco2e, 8.0)

    def test_from_file_missing(self):
        with self.assertRaises(FileNotFoundError):
            SCIOutput.from_file(os.path.join(self.temp_dir, "nope.json"))

    def test_from_file_malformed(self):
        path = self._write_context("{not json")
        with self.assertRaises(json.JSONDecodeError):
            SCIOutput.from_file(path, output_dir=self.temp_dir)


class _TrackerStub:
    """Minimal stand-in exercising ``_init_output_methods`` without hardware."""

    def __init__(self, output_dir: str, external_conf: dict):
        self._output_methods = [OutputMethod.SCI]
        self._emissions_endpoint = None
        self._external_conf = external_conf
        self._output_dir = output_dir
        self._output_handlers = []

    def init(self):
        BaseEmissionsTracker._init_output_methods(self, api_key=None)
        return self._output_handlers


class TestTrackerRegistration(unittest.TestCase):
    """Tracker registration of OutputMethod.SCI."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sci_method_adds_handler_without_declarations(self):
        handlers = _TrackerStub(self.temp_dir, {}).init()
        sci_handlers = [h for h in handlers if isinstance(h, SCIOutput)]
        self.assertEqual(len(sci_handlers), 1)
        self.assertIsNone(sci_handlers[0]._functional_unit)
        self.assertEqual(sci_handlers[0]._output_dir, self.temp_dir)

    def test_sci_context_file_from_config_is_loaded(self):
        context_path = os.path.join(self.temp_dir, "sci_context.json")
        with open(context_path, "w") as f:
            json.dump(
                {
                    "functionalUnit": {"name": "request", "count": 250},
                    "embodied": {"gCO2e": 12.0, "source": "vendor LCA"},
                },
                f,
            )
        handlers = _TrackerStub(
            self.temp_dir, {"sci_context_file": context_path}
        ).init()
        handler = next(h for h in handlers if isinstance(h, SCIOutput))
        self.assertEqual(handler._functional_unit, FunctionalUnit("request", 250))
        self.assertEqual(handler._embodied, EmbodiedDeclaration(12.0, "vendor LCA"))

    def test_sci_context_file_missing_degrades(self):
        with self.assertLogs("codecarbon", level="ERROR") as logs:
            handlers = _TrackerStub(
                self.temp_dir,
                {"sci_context_file": os.path.join(self.temp_dir, "nope.json")},
            ).init()
        self.assertTrue(any("sci_context_file" in m for m in logs.output))
        handler = next(h for h in handlers if isinstance(h, SCIOutput))
        self.assertIsNone(handler._functional_unit)


if __name__ == "__main__":
    unittest.main()
