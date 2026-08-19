"""Tests for the JSONOutput handler."""

import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest

from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData
from codecarbon.output_methods.json_output import JSONOutput


def _make_emissions_data(**overrides) -> EmissionsData:
    """Create a minimal EmissionsData for testing."""
    defaults = dict(
        timestamp="2024-01-01T00:00:00",
        project_name="test_project",
        run_id="test-run-id-001",
        experiment_id="test-exp-id",
        duration=60.0,
        emissions=0.001,
        emissions_rate=0.00001,
        cpu_power=50.0,
        gpu_power=100.0,
        ram_power=10.0,
        cpu_energy=0.0005,
        gpu_energy=0.001,
        ram_energy=0.0001,
        energy_consumed=0.0016,
        water_consumed=0.01,
        country_name="France",
        country_iso_code="FRA",
        region="ile-de-france",
        cloud_provider="",
        cloud_region="",
        os="Linux",
        python_version="3.11.0",
        codecarbon_version="3.3.0",
        cpu_count=8,
        cpu_model="Intel i7",
        gpu_count=1,
        gpu_model="NVIDIA RTX 4090",
        longitude=2.3522,
        latitude=48.8566,
        ram_total_size=32.0,
        tracking_mode="machine",
    )
    defaults.update(overrides)
    return EmissionsData(**defaults)


def _make_task_emissions_data(**overrides) -> TaskEmissionsData:
    """Create a minimal TaskEmissionsData for testing."""
    defaults = dict(
        task_name="training",
        timestamp="2024-01-01T00:00:00",
        project_name="test_project",
        run_id="test-run-id-001",
        duration=30.0,
        emissions=0.0005,
        emissions_rate=0.00001,
        cpu_power=50.0,
        gpu_power=100.0,
        ram_power=10.0,
        cpu_energy=0.00025,
        gpu_energy=0.0005,
        ram_energy=0.00005,
        energy_consumed=0.0008,
        water_consumed=0.005,
        country_name="France",
        country_iso_code="FRA",
        region="ile-de-france",
        cloud_provider="",
        cloud_region="",
        os="Linux",
        python_version="3.11.0",
        codecarbon_version="3.3.0",
        cpu_count=8,
        cpu_model="Intel i7",
        gpu_count=1,
        gpu_model="NVIDIA RTX 4090",
        longitude=2.3522,
        latitude=48.8566,
        ram_total_size=32.0,
        tracking_mode="machine",
    )
    defaults.update(overrides)
    return TaskEmissionsData(**defaults)


class TestJSONOutputInit:
    """Test JSONOutput initialization."""

    def test_init_creates_instance(self, tmp_path):
        output = JSONOutput(
            output_file_name="test.json",
            output_dir=str(tmp_path),
        )
        assert output.output_file_name == "test.json"
        assert output.output_dir == str(tmp_path)
        assert output.on_json_write == "append"

    def test_init_invalid_mode_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown"):
            JSONOutput(
                output_file_name="test.json",
                output_dir=str(tmp_path),
                on_json_write="invalid",
            )

    def test_init_nonexistent_dir_raises(self):
        with pytest.raises(OSError, match="doesn't exist"):
            JSONOutput(
                output_file_name="test.json",
                output_dir="/nonexistent/path/xyz",
            )

    def test_default_file_name(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path))
        assert output.output_file_name == "emissions.json"


class TestJSONOutputAppendMode:
    """Test JSONOutput in append (JSON Lines) mode."""

    def test_out_creates_file(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="append")
        data = _make_emissions_data()
        output.out(data, data)

        file_path = tmp_path / "emissions.json"
        assert file_path.exists()

    def test_out_writes_valid_json_line(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="append")
        data = _make_emissions_data()
        output.out(data, data)

        file_path = tmp_path / "emissions.json"
        with open(file_path) as f:
            line = f.readline().strip()
        parsed = json.loads(line)
        assert parsed["project_name"] == "test_project"
        assert parsed["run_id"] == "test-run-id-001"

    def test_out_appends_multiple_lines(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="append")
        data1 = _make_emissions_data(run_id="run-1")
        data2 = _make_emissions_data(run_id="run-2")
        output.out(data1, data1)
        output.out(data2, data2)

        file_path = tmp_path / "emissions.json"
        with open(file_path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["run_id"] == "run-1"
        assert json.loads(lines[1])["run_id"] == "run-2"


class TestJSONOutputOverwriteMode:
    """Test JSONOutput in overwrite mode."""

    def test_out_creates_json_array(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="overwrite")
        data = _make_emissions_data()
        output.out(data, data)

        file_path = tmp_path / "emissions.json"
        with open(file_path) as f:
            parsed = json.load(f)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_out_updates_existing_run(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="overwrite")
        data1 = _make_emissions_data(emissions=0.001)
        output.out(data1, data1)

        data2 = _make_emissions_data(emissions=0.002)
        output.out(data2, data2)

        file_path = tmp_path / "emissions.json"
        with open(file_path) as f:
            parsed = json.load(f)
        # Same run_id → should update, not duplicate
        assert len(parsed) == 1
        assert parsed[0]["emissions"] == 0.002

    def test_out_adds_new_run(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="overwrite")
        data1 = _make_emissions_data(run_id="run-1")
        data2 = _make_emissions_data(run_id="run-2")
        output.out(data1, data1)
        output.out(data2, data2)

        file_path = tmp_path / "emissions.json"
        with open(file_path) as f:
            parsed = json.load(f)
        assert len(parsed) == 2


class TestJSONOutputLiveOut:
    """Test live_out method."""

    def test_live_out_writes_data(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="append")
        data = _make_emissions_data()
        output.live_out(data, data)

        file_path = tmp_path / "emissions.json"
        assert file_path.exists()
        with open(file_path) as f:
            line = f.readline().strip()
        parsed = json.loads(line)
        assert parsed["run_id"] == "test-run-id-001"


class TestJSONOutputTaskOut:
    """Test task_out method."""

    def test_task_out_creates_task_file(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path))
        task_data = [_make_task_emissions_data()]
        output.task_out(task_data, "my_experiment")

        expected_file = tmp_path / "emissions_my_experiment_test-run-id-001.json"
        assert expected_file.exists()

    def test_task_out_writes_valid_json(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path))
        task_data = [
            _make_task_emissions_data(task_name="task1"),
            _make_task_emissions_data(task_name="task2"),
        ]
        output.task_out(task_data, "experiment")

        expected_file = tmp_path / "emissions_experiment_test-run-id-001.json"
        with open(expected_file) as f:
            parsed = json.load(f)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["task_name"] == "task1"
        assert parsed[1]["task_name"] == "task2"

    def test_task_out_empty_data_does_nothing(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path))
        output.task_out([], "experiment")
        # No file should be created
        assert len(list(tmp_path.iterdir())) == 0


class TestJSONOutputEdgeCases:
    """Test edge cases and error handling."""

    def test_read_existing_empty_file(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="overwrite")
        # Create an empty file
        (tmp_path / "emissions.json").write_text("")
        data = _make_emissions_data()
        output.out(data, data)

        with open(tmp_path / "emissions.json") as f:
            parsed = json.load(f)
        assert len(parsed) == 1

    def test_read_existing_invalid_json(self, tmp_path):
        output = JSONOutput(output_dir=str(tmp_path), on_json_write="overwrite")
        # Write invalid JSON
        (tmp_path / "emissions.json").write_text("not valid json {{{")
        data = _make_emissions_data()
        output.out(data, data)

        with open(tmp_path / "emissions.json") as f:
            parsed = json.load(f)
        assert len(parsed) == 1
