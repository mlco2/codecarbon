"""
Comprehensive test suite for BoAmps output support.

Tests organized as documentation sections covering:
A. Model serialization
B. EmissionsData -> BoAmps mapping
C. Output handler
D. Schema validation
E. Context file loading
F. Integration
"""

import json
import os
import shutil
import tempfile
import unittest
import warnings

from codecarbon.output_methods.boamps.mapper import (
    BOAMPS_FORMAT_VERSION,
    map_emissions_to_boamps,
)
from codecarbon.output_methods.boamps.models import (
    BoAmpsAlgorithm,
    BoAmpsDataset,
    BoAmpsEnvironment,
    BoAmpsHardware,
    BoAmpsHeader,
    BoAmpsInfrastructure,
    BoAmpsMeasure,
    BoAmpsPublisher,
    BoAmpsReport,
    BoAmpsSoftware,
    BoAmpsSystem,
    BoAmpsTask,
    camel_to_snake,
    snake_to_camel,
)
from codecarbon.output_methods.boamps.output import BoAmpsOutput
from codecarbon.output_methods.emissions_data import EmissionsData


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
        region="Ile-de-France",
        cloud_provider="",
        cloud_region="",
        os="Linux-5.15.0",
        python_version="3.11.5",
        codecarbon_version="2.5.0",
        cpu_count=8,
        cpu_model="Intel Core i7-12700",
        gpu_count=1,
        gpu_model="NVIDIA RTX 3090",
        longitude=2.3522,
        latitude=48.8566,
        ram_total_size=32.0,
        tracking_mode="machine",
        cpu_utilization_percent=65.0,
        gpu_utilization_percent=80.0,
        on_cloud="N",
    )
    defaults.update(overrides)
    return EmissionsData(**defaults)


def _make_task() -> BoAmpsTask:
    """Create a minimal valid BoAmps task for testing."""
    return BoAmpsTask(
        task_stage="inference",
        task_family="chatbot",
        algorithms=[
            BoAmpsAlgorithm(
                algorithm_type="llm",
                foundation_model_name="llama3.1-8b",
            )
        ],
        dataset=[
            BoAmpsDataset(data_usage="input", data_type="token", data_quantity=50),
            BoAmpsDataset(data_usage="output", data_type="token", data_quantity=200),
        ],
    )


# ===========================================================================
# A. BoAmps Model Serialization Tests
# ===========================================================================


class TestModelSerialization(unittest.TestCase):
    """Each model serializes to correct camelCase JSON structure."""

    def test_snake_to_camel_conversion(self):
        self.assertEqual(snake_to_camel("measurement_method"), "measurementMethod")
        self.assertEqual(snake_to_camel("cpu_tracking_mode"), "cpuTrackingMode")
        self.assertEqual(snake_to_camel("os"), "os")
        self.assertEqual(snake_to_camel("nb_component"), "nbComponent")
        self.assertEqual(
            snake_to_camel("format_version_specification_uri"),
            "formatVersionSpecificationUri",
        )

    def test_camel_to_snake_conversion(self):
        self.assertEqual(camel_to_snake("measurementMethod"), "measurement_method")
        self.assertEqual(camel_to_snake("cpuTrackingMode"), "cpu_tracking_mode")
        self.assertEqual(camel_to_snake("os"), "os")
        self.assertEqual(camel_to_snake("nbComponent"), "nb_component")

    def test_publisher_serialization(self):
        pub = BoAmpsPublisher(
            name="Test Org",
            confidentiality_level="public",
        )
        d = pub.to_dict()
        self.assertEqual(d["name"], "Test Org")
        self.assertEqual(d["confidentialityLevel"], "public")
        self.assertNotIn("division", d)  # None stripped

    def test_header_serialization(self):
        header = BoAmpsHeader(
            report_id="abc-123",
            report_datetime="2025-01-15T10:30:00",
            format_version="0.1",
        )
        d = header.to_dict()
        self.assertEqual(d["reportId"], "abc-123")
        self.assertEqual(d["reportDatetime"], "2025-01-15T10:30:00")
        self.assertEqual(d["formatVersion"], "0.1")
        self.assertNotIn("licensing", d)

    def test_algorithm_serialization(self):
        algo = BoAmpsAlgorithm(
            algorithm_type="llm",
            foundation_model_name="llama3.1-8b",
            parameters_number=8,
        )
        d = algo.to_dict()
        self.assertEqual(d["algorithmType"], "llm")
        self.assertEqual(d["foundationModelName"], "llama3.1-8b")
        self.assertEqual(d["parametersNumber"], 8)
        self.assertNotIn("trainingType", d)

    def test_dataset_serialization(self):
        ds = BoAmpsDataset(
            data_usage="input",
            data_type="token",
            data_quantity=50,
        )
        d = ds.to_dict()
        self.assertEqual(d["dataUsage"], "input")
        self.assertEqual(d["dataType"], "token")
        self.assertEqual(d["dataQuantity"], 50)

    def test_task_serialization_with_nested_lists(self):
        task = _make_task()
        d = task.to_dict()
        self.assertEqual(d["taskStage"], "inference")
        self.assertEqual(d["taskFamily"], "chatbot")
        self.assertEqual(len(d["algorithms"]), 1)
        self.assertEqual(d["algorithms"][0]["algorithmType"], "llm")
        self.assertEqual(len(d["dataset"]), 2)
        self.assertEqual(d["dataset"][0]["dataUsage"], "input")
        self.assertEqual(d["dataset"][1]["dataUsage"], "output")

    def test_measure_serialization(self):
        m = BoAmpsMeasure(
            measurement_method="codecarbon",
            power_consumption=0.1007,
            measurement_duration=3600.0,
            average_utilization_cpu=0.65,
        )
        d = m.to_dict()
        self.assertEqual(d["measurementMethod"], "codecarbon")
        self.assertEqual(d["powerConsumption"], 0.1007)
        self.assertEqual(d["measurementDuration"], 3600.0)
        self.assertEqual(d["averageUtilizationCpu"], 0.65)

    def test_hardware_serialization(self):
        hw = BoAmpsHardware(
            component_type="gpu",
            component_name="NVIDIA RTX 3090",
            nb_component=1,
        )
        d = hw.to_dict()
        self.assertEqual(d["componentType"], "gpu")
        self.assertEqual(d["componentName"], "NVIDIA RTX 3090")
        self.assertEqual(d["nbComponent"], 1)

    def test_infrastructure_serialization(self):
        infra = BoAmpsInfrastructure(
            infra_type="onPremise",
            components=[
                BoAmpsHardware(component_type="cpu", nb_component=1),
                BoAmpsHardware(component_type="ram", nb_component=1, memory_size=32.0),
            ],
        )
        d = infra.to_dict()
        self.assertEqual(d["infraType"], "onPremise")
        self.assertEqual(len(d["components"]), 2)
        self.assertEqual(d["components"][0]["componentType"], "cpu")

    def test_none_values_stripped_from_output(self):
        """None values should not appear in serialized output."""
        report = BoAmpsReport(
            header=BoAmpsHeader(report_id="test"),
            quality=None,
        )
        d = report.to_dict()
        self.assertNotIn("quality", d)
        self.assertNotIn("task", d)
        self.assertNotIn("measures", d)

    def test_full_report_serialization(self):
        """Complete report with all sections serializes correctly."""
        report = BoAmpsReport(
            header=BoAmpsHeader(report_id="test-123", format_version="0.1"),
            task=_make_task(),
            measures=[
                BoAmpsMeasure(measurement_method="codecarbon", power_consumption=0.1)
            ],
            system=BoAmpsSystem(os="Linux"),
            software=BoAmpsSoftware(language="python", version="3.11"),
            infrastructure=BoAmpsInfrastructure(
                infra_type="onPremise",
                components=[BoAmpsHardware(component_type="cpu", nb_component=1)],
            ),
            environment=BoAmpsEnvironment(country="France"),
            quality="high",
        )
        d = report.to_dict()
        self.assertIn("header", d)
        self.assertIn("task", d)
        self.assertIn("measures", d)
        self.assertIn("system", d)
        self.assertIn("software", d)
        self.assertIn("infrastructure", d)
        self.assertIn("environment", d)
        self.assertEqual(d["quality"], "high")

    def test_report_serializes_to_valid_json(self):
        """Report.to_dict() result is JSON-serializable."""
        report = BoAmpsReport(
            header=BoAmpsHeader(report_id="test"),
            task=_make_task(),
            measures=[
                BoAmpsMeasure(measurement_method="codecarbon", power_consumption=0.1)
            ],
            infrastructure=BoAmpsInfrastructure(
                infra_type="onPremise",
                components=[BoAmpsHardware(component_type="cpu", nb_component=1)],
            ),
        )
        json_str = json.dumps(report.to_dict(), indent=2)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["header"]["reportId"], "test")


# ===========================================================================
# B. EmissionsData -> BoAmps Mapping Tests
# ===========================================================================


class TestEmissionsMapping(unittest.TestCase):
    """Full mapping from EmissionsData to BoAmps report."""

    def setUp(self):
        self.emissions = _make_emissions_data()
        self.task = _make_task()

    def test_full_mapping(self):
        """Realistic EmissionsData maps to a complete BoAmps report."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        d = report.to_dict()

        # All major sections present
        self.assertIn("header", d)
        self.assertIn("task", d)
        self.assertIn("measures", d)
        self.assertIn("system", d)
        self.assertIn("software", d)
        self.assertIn("infrastructure", d)
        self.assertIn("environment", d)

    def test_header_auto_population(self):
        """run_id -> reportId, timestamp -> reportDatetime."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        header = report.header.to_dict()
        self.assertEqual(header["reportId"], self.emissions.run_id)
        self.assertEqual(header["reportDatetime"], self.emissions.timestamp)
        self.assertEqual(header["formatVersion"], BOAMPS_FORMAT_VERSION)

    def test_measures_mapping(self):
        """energy_consumed -> powerConsumption, duration -> measurementDuration."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        measure = report.measures[0].to_dict()
        self.assertEqual(measure["measurementMethod"], "codecarbon")
        self.assertEqual(measure["version"], self.emissions.codecarbon_version)
        self.assertEqual(measure["powerConsumption"], self.emissions.energy_consumed)
        self.assertEqual(measure["measurementDuration"], self.emissions.duration)
        self.assertEqual(measure["measurementDateTime"], self.emissions.timestamp)
        self.assertEqual(measure["cpuTrackingMode"], self.emissions.tracking_mode)

    def test_cpu_utilization_as_fraction(self):
        """cpu_utilization_percent is converted to 0-1 range."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        measure = report.measures[0].to_dict()
        self.assertAlmostEqual(measure["averageUtilizationCpu"], 0.65, places=2)

    def test_gpu_utilization_as_fraction(self):
        """gpu_utilization_percent is converted to 0-1 range when GPU present."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        measure = report.measures[0].to_dict()
        self.assertAlmostEqual(measure["averageUtilizationGpu"], 0.80, places=2)

    def test_gpu_tracking_mode_set_when_gpu_present(self):
        """gpuTrackingMode is set when gpu_count > 0."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        measure = report.measures[0].to_dict()
        self.assertIn("gpuTrackingMode", measure)

    def test_infrastructure_decomposition(self):
        """CPU, GPU, RAM as separate components[]."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        infra = report.infrastructure.to_dict()
        component_types = [c["componentType"] for c in infra["components"]]
        self.assertIn("cpu", component_types)
        self.assertIn("gpu", component_types)
        self.assertIn("ram", component_types)

    def test_cpu_component_details(self):
        """cpu_count (threads) is halved to approximate physical cores."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        cpu = [
            c for c in report.infrastructure.components if c.component_type == "cpu"
        ][0]
        self.assertEqual(cpu.component_name, "Intel Core i7-12700")
        # emissions.cpu_count=8 threads -> 4 cores (SMT/HT heuristic)
        self.assertEqual(cpu.nb_component, 4)

    def test_gpu_component_details(self):
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        gpu = [
            c for c in report.infrastructure.components if c.component_type == "gpu"
        ][0]
        self.assertEqual(gpu.component_name, "NVIDIA RTX 3090")
        self.assertEqual(gpu.nb_component, 1)

    def test_ram_component_details(self):
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        ram = [
            c for c in report.infrastructure.components if c.component_type == "ram"
        ][0]
        self.assertEqual(ram.memory_size, 32.0)
        self.assertEqual(ram.nb_component, 1)

    def test_gpu_omitted_when_no_gpu(self):
        """GPU component is omitted when gpu_count=0 and gpu_model is empty."""
        emissions = _make_emissions_data(
            gpu_count=0,
            gpu_model="",
            gpu_power=0.0,
            gpu_energy=0.0,
            gpu_utilization_percent=0.0,
        )
        report = map_emissions_to_boamps(emissions, task=self.task)
        component_types = [c.component_type for c in report.infrastructure.components]
        self.assertNotIn("gpu", component_types)
        self.assertIn("cpu", component_types)
        self.assertIn("ram", component_types)

    def test_gpu_tracking_mode_omitted_when_no_gpu(self):
        """gpuTrackingMode not set when no GPU."""
        emissions = _make_emissions_data(
            gpu_count=0, gpu_model="", gpu_utilization_percent=0.0
        )
        report = map_emissions_to_boamps(emissions, task=self.task)
        measure = report.measures[0].to_dict()
        self.assertNotIn("gpuTrackingMode", measure)
        self.assertNotIn("averageUtilizationGpu", measure)

    def test_on_premise_detection(self):
        """on_cloud='N' -> infraType='onPremise'."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        self.assertEqual(report.infrastructure.infra_type, "onPremise")

    def test_cloud_detection(self):
        """on_cloud='Y' -> infraType='publicCloud' with cloud_provider."""
        emissions = _make_emissions_data(
            on_cloud="Y",
            cloud_provider="aws",
            cloud_region="us-east-1",
        )
        report = map_emissions_to_boamps(emissions, task=self.task)
        self.assertEqual(report.infrastructure.infra_type, "publicCloud")
        self.assertEqual(report.infrastructure.cloud_provider, "aws")

    def test_cloud_detection_from_provider_when_on_cloud_is_N(self):
        """cloud_provider is used as secondary signal when on_cloud='N'."""
        emissions = _make_emissions_data(
            on_cloud="N",
            cloud_provider="aws",
            cloud_region="us-east-1",
        )
        report = map_emissions_to_boamps(emissions, task=self.task)
        self.assertEqual(report.infrastructure.infra_type, "publicCloud")
        self.assertEqual(report.infrastructure.cloud_provider, "aws")

    def test_environment_mapping(self):
        """country_name, latitude, longitude map to environment."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        env = report.environment.to_dict()
        self.assertEqual(env["country"], "France")
        self.assertAlmostEqual(env["latitude"], 48.8566)
        self.assertAlmostEqual(env["longitude"], 2.3522)

    def test_zero_latitude_longitude_preserved(self):
        """Valid 0.0 lat/lon (equator/prime meridian) are not dropped."""
        emissions = _make_emissions_data(latitude=0.0, longitude=0.0)
        report = map_emissions_to_boamps(emissions, task=self.task)
        env = report.environment.to_dict()
        self.assertEqual(env["latitude"], 0.0)
        self.assertEqual(env["longitude"], 0.0)

    def test_system_mapping(self):
        """os field maps to system.os."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        self.assertEqual(report.system.os, "Linux-5.15.0")

    def test_software_mapping(self):
        """language='python', version from python_version."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        self.assertEqual(report.software.language, "python")
        self.assertEqual(report.software.version, "3.11.5")

    def test_user_task_preserved(self):
        """User-provided task context is preserved and merged."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        task_dict = report.task.to_dict()
        self.assertEqual(task_dict["taskStage"], "inference")
        self.assertEqual(task_dict["taskFamily"], "chatbot")
        self.assertEqual(len(task_dict["algorithms"]), 1)
        self.assertEqual(len(task_dict["dataset"]), 2)

    def test_user_header_overrides(self):
        """User header values take precedence over auto-detected."""
        user_header = BoAmpsHeader(
            licensing="CC-BY-4.0",
            report_status="final",
            publisher=BoAmpsPublisher(name="My Org", confidentiality_level="public"),
        )
        report = map_emissions_to_boamps(
            self.emissions, task=self.task, header=user_header
        )
        header = report.header.to_dict()
        self.assertEqual(header["licensing"], "CC-BY-4.0")
        self.assertEqual(header["reportStatus"], "final")
        self.assertEqual(header["publisher"]["name"], "My Org")
        # Auto-detected fields still present
        self.assertEqual(header["reportId"], self.emissions.run_id)
        self.assertEqual(header["formatVersion"], BOAMPS_FORMAT_VERSION)

    def test_quality_passthrough(self):
        report = map_emissions_to_boamps(self.emissions, task=self.task, quality="high")
        self.assertEqual(report.quality, "high")

    def test_infra_overrides(self):
        """Infrastructure overrides are applied."""
        overrides = {"cloud_instance": "p3.2xlarge", "cloud_service": "EC2"}
        report = map_emissions_to_boamps(
            self.emissions, task=self.task, infra_overrides=overrides
        )
        self.assertEqual(report.infrastructure.cloud_instance, "p3.2xlarge")
        self.assertEqual(report.infrastructure.cloud_service, "EC2")

    def test_environment_overrides(self):
        """Environment overrides are applied."""
        overrides = {"power_source": "nuclear", "power_source_carbon_intensity": 12.0}
        report = map_emissions_to_boamps(
            self.emissions, task=self.task, environment_overrides=overrides
        )
        self.assertEqual(report.environment.power_source, "nuclear")
        self.assertEqual(report.environment.power_source_carbon_intensity, 12.0)

    def test_warning_when_no_task(self):
        """Warns when required BoAmps task fields are missing."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            map_emissions_to_boamps(self.emissions, task=None)
            self.assertEqual(len(w), 1)
            self.assertIn("task", str(w[0].message).lower())


# ===========================================================================
# C. BoAmps Output Handler Tests
# ===========================================================================


class TestBoAmpsOutputHandler(unittest.TestCase):
    """Output handler writes valid JSON files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.emissions = _make_emissions_data()
        self.task = _make_task()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_out_writes_json_file(self):
        """BoAmpsOutput.out() writes a valid JSON file."""
        handler = BoAmpsOutput(output_dir=self.tmpdir, task=self.task)
        handler.out(self.emissions, self.emissions)

        expected_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        self.assertTrue(os.path.isfile(expected_file))

        with open(expected_file) as f:
            report = json.load(f)
        self.assertIn("header", report)
        self.assertIn("measures", report)

    def test_output_file_naming(self):
        """Output file is named boamps_report_{run_id}.json."""
        handler = BoAmpsOutput(output_dir=self.tmpdir, task=self.task)
        handler.out(self.emissions, self.emissions)

        files = os.listdir(self.tmpdir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith("boamps_report_"))
        self.assertTrue(files[0].endswith(".json"))
        self.assertIn(self.emissions.run_id, files[0])

    def test_handler_programmatic_config(self):
        """Handler can be constructed with programmatic config."""
        handler = BoAmpsOutput(
            output_dir=self.tmpdir,
            task=self.task,
            quality="high",
            header=BoAmpsHeader(licensing="CC-BY-4.0"),
        )
        handler.out(self.emissions, self.emissions)

        expected_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(expected_file) as f:
            report = json.load(f)
        self.assertEqual(report["quality"], "high")
        self.assertEqual(report["header"]["licensing"], "CC-BY-4.0")

    def test_live_out_is_noop(self):
        """live_out() is a no-op (BoAmps reports are final)."""
        handler = BoAmpsOutput(output_dir=self.tmpdir, task=self.task)
        handler.live_out(self.emissions, self.emissions)
        # No files should be created
        self.assertEqual(len(os.listdir(self.tmpdir)), 0)

    def test_output_contains_all_auto_fields(self):
        """Output JSON contains all auto-filled fields from EmissionsData."""
        handler = BoAmpsOutput(output_dir=self.tmpdir, task=self.task)
        handler.out(self.emissions, self.emissions)

        expected_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(expected_file) as f:
            report = json.load(f)

        # Header
        self.assertEqual(report["header"]["reportId"], self.emissions.run_id)
        self.assertEqual(report["header"]["reportDatetime"], self.emissions.timestamp)
        # Measures
        self.assertEqual(report["measures"][0]["measurementMethod"], "codecarbon")
        self.assertEqual(
            report["measures"][0]["powerConsumption"],
            self.emissions.energy_consumed,
        )
        # System
        self.assertEqual(report["system"]["os"], self.emissions.os)
        # Software
        self.assertEqual(report["software"]["language"], "python")
        # Infrastructure
        self.assertEqual(report["infrastructure"]["infraType"], "onPremise")
        # Environment
        self.assertEqual(report["environment"]["country"], "France")

    def test_minimal_handler_warns(self):
        """Minimal handler (no task) warns about missing fields."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            handler = BoAmpsOutput(output_dir=self.tmpdir)
            handler.out(self.emissions, self.emissions)
            self.assertTrue(
                any("task" in str(warning.message).lower() for warning in w)
            )


# ===========================================================================
# D. Schema Validation Tests
# ===========================================================================


class TestSchemaValidation(unittest.TestCase):
    """Validate output against the actual BoAmps JSON schemas."""

    # Vendored from https://github.com/Boavizta/BoAmps/tree/main/model (v0.1)
    SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "boamps_schemas")

    @classmethod
    def _load_schemas(cls):
        """Load all BoAmps schemas and create a resolver."""
        try:
            from jsonschema import Draft4Validator, RefResolver
        except ImportError:
            return None, None

        schema_files = [
            "report_schema.json",
            "algorithm_schema.json",
            "dataset_schema.json",
            "hardware_schema.json",
            "measure_schema.json",
        ]
        store = {}
        report_schema = None
        for fname in schema_files:
            path = os.path.join(cls.SCHEMA_DIR, fname)
            if not os.path.isfile(path):
                return None, None
            with open(path) as f:
                schema = json.load(f)
            store[schema["id"]] = schema
            if fname == "report_schema.json":
                report_schema = schema

        resolver = RefResolver.from_schema(report_schema, store=store)
        validator = Draft4Validator(report_schema, resolver=resolver)
        return validator, report_schema

    def setUp(self):
        self.validator, self.schema = self._load_schemas()
        if self.validator is None:
            self.skipTest(
                "jsonschema not installed or BoAmps schemas not found at "
                f"{self.SCHEMA_DIR}"
            )
        self.emissions = _make_emissions_data()
        self.task = _make_task()

    def test_minimal_valid_report_passes(self):
        """Minimal valid report (auto-filled + minimal task) passes validation."""
        report = map_emissions_to_boamps(self.emissions, task=self.task)
        report_dict = report.to_dict()
        errors = list(self.validator.iter_errors(report_dict))
        self.assertEqual(
            errors,
            [],
            f"Validation errors: {[e.message for e in errors]}",
        )

    def test_full_report_passes(self):
        """Full report with all optional fields passes validation."""
        report = map_emissions_to_boamps(
            self.emissions,
            task=BoAmpsTask(
                task_stage="training",
                task_family="text classification",
                nb_request=0,
                algorithms=[
                    BoAmpsAlgorithm(
                        algorithm_type="neural network",
                        algorithm_name="transformers",
                        training_type="supervisedLearning",
                        framework="pytorch",
                        framework_version="2.1.0",
                        parameters_number=0.125,
                        epochs_number=10,
                        quantization="fp16",
                    )
                ],
                dataset=[
                    BoAmpsDataset(
                        data_usage="input",
                        data_type="text",
                        data_format="csv",
                        data_size=2.5,
                        data_quantity=50000,
                        shape="(50000, 128)",
                        source="public",
                    )
                ],
                measured_accuracy=0.95,
                task_description="Fine-tuning BERT for sentiment analysis",
            ),
            header=BoAmpsHeader(
                licensing="CC-BY-4.0",
                report_status="final",
                publisher=BoAmpsPublisher(
                    name="Test Org",
                    division="ML Team",
                    confidentiality_level="public",
                ),
            ),
            quality="high",
            environment_overrides={
                "power_source": "nuclear",
                "power_source_carbon_intensity": 12.0,
            },
        )
        report_dict = report.to_dict()
        errors = list(self.validator.iter_errors(report_dict))
        self.assertEqual(
            errors,
            [],
            f"Validation errors: {[e.message for e in errors]}",
        )

    def test_report_without_task_fails_schema(self):
        """Report without required task section fails validation."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            report = map_emissions_to_boamps(self.emissions, task=None)
        report_dict = report.to_dict()
        errors = list(self.validator.iter_errors(report_dict))
        required_missing = any("task" in e.message for e in errors)
        self.assertTrue(
            required_missing,
            "Expected validation error for missing 'task' field",
        )


# ===========================================================================
# E. Context File Loading Tests
# ===========================================================================


class TestContextFileLoading(unittest.TestCase):
    """Loading and merging BoAmps context files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.emissions = _make_emissions_data()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_context_file(self, context: dict) -> str:
        path = os.path.join(self.tmpdir, "boamps_context.json")
        with open(path, "w") as f:
            json.dump(context, f)
        return path

    def test_load_valid_context_file(self):
        """Load a valid BoAmps context file."""
        context = {
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "algorithms": [{"algorithmType": "llm"}],
                "dataset": [{"dataUsage": "input", "dataType": "token"}],
            },
            "quality": "high",
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        self.assertIsNotNone(handler._task)
        self.assertEqual(handler._task.task_stage, "inference")
        self.assertEqual(handler._quality, "high")

    def test_merge_context_with_auto_detected(self):
        """Context file fields merge with auto-detected EmissionsData fields."""
        context = {
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "algorithms": [{"algorithmType": "llm"}],
                "dataset": [{"dataUsage": "input", "dataType": "token"}],
            },
            "header": {
                "licensing": "CC-BY-4.0",
                "reportStatus": "draft",
                "publisher": {"name": "My Org", "confidentialityLevel": "public"},
            },
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        handler.out(self.emissions, self.emissions)

        report_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(report_file) as f:
            report = json.load(f)

        # Context file values
        self.assertEqual(report["header"]["licensing"], "CC-BY-4.0")
        self.assertEqual(report["header"]["publisher"]["name"], "My Org")
        # Auto-detected values
        self.assertEqual(report["header"]["reportId"], self.emissions.run_id)
        self.assertEqual(report["measures"][0]["measurementMethod"], "codecarbon")

    def test_context_file_task_overrides(self):
        """Context file task values are preserved."""
        context = {
            "task": {
                "taskStage": "training",
                "taskFamily": "image generation",
                "algorithms": [
                    {
                        "algorithmType": "neural network",
                        "foundationModelName": "stable-diffusion",
                    }
                ],
                "dataset": [
                    {"dataUsage": "input", "dataType": "image", "dataQuantity": 10000}
                ],
            },
            "quality": "medium",
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        self.assertEqual(handler._task.task_stage, "training")
        self.assertEqual(handler._task.task_family, "image generation")
        self.assertEqual(
            handler._task.algorithms[0].foundation_model_name, "stable-diffusion"
        )
        self.assertEqual(handler._quality, "medium")

    def test_invalid_context_file_path_raises(self):
        """Invalid context file path raises clear error."""
        with self.assertRaises(FileNotFoundError) as ctx:
            BoAmpsOutput.from_file("/nonexistent/path.json")
        self.assertIn("not found", str(ctx.exception))

    def test_malformed_json_raises(self):
        """Malformed JSON context file raises clear error."""
        path = os.path.join(self.tmpdir, "bad.json")
        with open(path, "w") as f:
            f.write("{not valid json")
        with self.assertRaises(json.JSONDecodeError):
            BoAmpsOutput.from_file(path)

    def test_context_with_infrastructure_overrides(self):
        """Infrastructure fields from context file are applied as overrides."""
        context = {
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "algorithms": [{"algorithmType": "llm"}],
                "dataset": [{"dataUsage": "input", "dataType": "token"}],
            },
            "infrastructure": {
                "cloudInstance": "p3.2xlarge",
                "cloudService": "EC2",
            },
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        handler.out(self.emissions, self.emissions)

        report_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(report_file) as f:
            report = json.load(f)
        self.assertEqual(report["infrastructure"]["cloudInstance"], "p3.2xlarge")
        self.assertEqual(report["infrastructure"]["cloudService"], "EC2")

    def test_context_with_environment_overrides(self):
        """Environment fields from context file are applied as overrides."""
        context = {
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "algorithms": [{"algorithmType": "llm"}],
                "dataset": [{"dataUsage": "input", "dataType": "token"}],
            },
            "environment": {
                "powerSource": "nuclear",
                "powerSourceCarbonIntensity": 12.0,
            },
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        handler.out(self.emissions, self.emissions)

        report_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(report_file) as f:
            report = json.load(f)
        self.assertEqual(report["environment"]["powerSource"], "nuclear")
        self.assertEqual(report["environment"]["powerSourceCarbonIntensity"], 12.0)

    def test_context_with_user_components(self):
        """User-provided components enrich auto-detected ones."""
        context = {
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "algorithms": [{"algorithmType": "llm"}],
                "dataset": [{"dataUsage": "input", "dataType": "token"}],
            },
            "infrastructure": {
                "components": [
                    {
                        "componentType": "gpu",
                        "nbComponent": 1,
                        "manufacturer": "nvidia",
                        "family": "geforce",
                        "series": "rtx3090",
                    }
                ],
            },
        }
        path = self._write_context_file(context)
        handler = BoAmpsOutput.from_file(path, output_dir=self.tmpdir)
        handler.out(self.emissions, self.emissions)

        report_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        with open(report_file) as f:
            report = json.load(f)
        components = report["infrastructure"]["components"]
        gpu = [c for c in components if c["componentType"] == "gpu"][0]
        # User-provided details preserved
        self.assertEqual(gpu["manufacturer"], "nvidia")
        self.assertEqual(gpu["family"], "geforce")
        self.assertEqual(gpu["series"], "rtx3090")
        # Auto-detected name filled in since user didn't provide it
        self.assertEqual(gpu["componentName"], "NVIDIA RTX 3090")
        # Auto-detected CPU and RAM still present
        component_types = [c["componentType"] for c in components]
        self.assertIn("cpu", component_types)
        self.assertIn("ram", component_types)


# ===========================================================================
# F. Model from_dict / round-trip Tests
# ===========================================================================


class TestModelDeserialization(unittest.TestCase):
    """Models can be loaded from camelCase dicts (e.g., context files)."""

    def test_algorithm_from_dict(self):
        d = {"algorithmType": "llm", "foundationModelName": "llama3.1-8b"}
        algo = BoAmpsAlgorithm.from_dict(d)
        self.assertEqual(algo.algorithm_type, "llm")
        self.assertEqual(algo.foundation_model_name, "llama3.1-8b")

    def test_dataset_from_dict(self):
        d = {"dataUsage": "input", "dataType": "token", "dataQuantity": 50}
        ds = BoAmpsDataset.from_dict(d)
        self.assertEqual(ds.data_usage, "input")
        self.assertEqual(ds.data_type, "token")
        self.assertEqual(ds.data_quantity, 50)

    def test_task_from_dict_with_nested(self):
        d = {
            "taskStage": "inference",
            "taskFamily": "chatbot",
            "algorithms": [{"algorithmType": "llm"}],
            "dataset": [{"dataUsage": "input", "dataType": "token"}],
        }
        task = BoAmpsTask.from_dict(d)
        self.assertEqual(task.task_stage, "inference")
        self.assertIsInstance(task.algorithms[0], BoAmpsAlgorithm)
        self.assertIsInstance(task.dataset[0], BoAmpsDataset)

    def test_header_from_dict_with_publisher(self):
        d = {
            "licensing": "CC-BY-4.0",
            "publisher": {"name": "Org", "confidentialityLevel": "public"},
        }
        header = BoAmpsHeader.from_dict(d)
        self.assertEqual(header.licensing, "CC-BY-4.0")
        self.assertIsInstance(header.publisher, BoAmpsPublisher)
        self.assertEqual(header.publisher.name, "Org")

    def test_infrastructure_from_dict_with_components(self):
        d = {
            "infraType": "onPremise",
            "components": [
                {"componentType": "cpu", "nbComponent": 1},
                {"componentType": "gpu", "nbComponent": 2},
            ],
        }
        infra = BoAmpsInfrastructure.from_dict(d)
        self.assertEqual(infra.infra_type, "onPremise")
        self.assertEqual(len(infra.components), 2)
        self.assertIsInstance(infra.components[0], BoAmpsHardware)

    def test_report_from_dict_roundtrip(self):
        """Report can survive a to_dict -> from_dict roundtrip."""
        original = BoAmpsReport(
            header=BoAmpsHeader(report_id="test", format_version="0.1"),
            task=_make_task(),
            measures=[
                BoAmpsMeasure(measurement_method="codecarbon", power_consumption=0.1)
            ],
            system=BoAmpsSystem(os="Linux"),
            software=BoAmpsSoftware(language="python", version="3.11"),
            infrastructure=BoAmpsInfrastructure(
                infra_type="onPremise",
                components=[BoAmpsHardware(component_type="cpu", nb_component=1)],
            ),
            environment=BoAmpsEnvironment(country="France"),
            quality="high",
        )
        d = original.to_dict()
        restored = BoAmpsReport.from_dict(d)
        self.assertEqual(restored.header.report_id, "test")
        self.assertEqual(restored.task.task_stage, "inference")
        self.assertEqual(restored.measures[0].measurement_method, "codecarbon")
        self.assertEqual(restored.quality, "high")
        # Re-serialize and compare
        self.assertEqual(original.to_dict(), restored.to_dict())


# ===========================================================================
# G. Integration Test
# ===========================================================================


class TestIntegration(unittest.TestCase):
    """Full lifecycle: create handler, process emissions, verify output."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.emissions = _make_emissions_data()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _read_report(self) -> dict:
        report_file = os.path.join(
            self.tmpdir, f"boamps_report_{self.emissions.run_id}.json"
        )
        self.assertTrue(os.path.isfile(report_file))
        with open(report_file) as f:
            return json.load(f)

    def test_full_lifecycle(self):
        """BoAmpsOutput produces a valid report from EmissionsData."""
        handler = BoAmpsOutput(
            output_dir=self.tmpdir,
            task=_make_task(),
            quality="high",
            header=BoAmpsHeader(
                licensing="CC-BY-4.0",
                publisher=BoAmpsPublisher(
                    name="Test Lab", confidentiality_level="public"
                ),
            ),
        )
        handler.out(self.emissions, self.emissions)
        report = self._read_report()

        # All sections present
        for section in (
            "header",
            "task",
            "measures",
            "system",
            "software",
            "infrastructure",
            "environment",
        ):
            self.assertIn(section, report)
        self.assertEqual(report["quality"], "high")

        # Auto-filled
        self.assertEqual(report["header"]["reportId"], self.emissions.run_id)
        self.assertEqual(report["measures"][0]["measurementMethod"], "codecarbon")
        self.assertEqual(report["system"]["os"], self.emissions.os)
        self.assertEqual(report["software"]["language"], "python")

        # User-provided
        self.assertEqual(report["task"]["taskStage"], "inference")
        self.assertEqual(report["header"]["licensing"], "CC-BY-4.0")
        self.assertEqual(report["header"]["publisher"]["name"], "Test Lab")

    def test_context_file_lifecycle(self):
        """Full lifecycle using from_file() constructor."""
        context = {
            "header": {
                "licensing": "MIT",
                "reportStatus": "draft",
                "publisher": {
                    "name": "Test Corp",
                    "confidentialityLevel": "internal",
                },
            },
            "task": {
                "taskStage": "inference",
                "taskFamily": "chatbot",
                "nbRequest": 100,
                "algorithms": [
                    {
                        "algorithmType": "llm",
                        "foundationModelName": "llama3.1-8b",
                        "parametersNumber": 8,
                    }
                ],
                "dataset": [
                    {"dataUsage": "input", "dataType": "token", "dataQuantity": 50},
                    {"dataUsage": "output", "dataType": "token", "dataQuantity": 200},
                ],
            },
            "quality": "high",
        }
        context_path = os.path.join(self.tmpdir, "boamps_context.json")
        with open(context_path, "w") as f:
            json.dump(context, f)

        handler = BoAmpsOutput.from_file(context_path, output_dir=self.tmpdir)
        handler.out(self.emissions, self.emissions)
        report = self._read_report()

        self.assertEqual(report["task"]["taskStage"], "inference")
        self.assertEqual(report["task"]["nbRequest"], 100)
        self.assertEqual(
            report["task"]["algorithms"][0]["foundationModelName"], "llama3.1-8b"
        )
        self.assertEqual(report["header"]["licensing"], "MIT")
        self.assertEqual(report["header"]["publisher"]["name"], "Test Corp")
        self.assertEqual(report["quality"], "high")
        # Auto-detected still present
        self.assertEqual(report["measures"][0]["measurementMethod"], "codecarbon")


if __name__ == "__main__":
    unittest.main()
