"""
Tests for FileOutput.live_out() periodic CSV flushing.
Verifies that emissions data is written to CSV periodically during a run,
not just at the end. Fixes issue #448.
"""

import os

import pandas as pd
import pytest

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.file import FileOutput


def make_emissions_data(run_id="test-run-123", emissions=0.001):
    """Helper to create a minimal EmissionsData object for testing."""
    return EmissionsData(
        timestamp="2024-01-01T00:00:00",
        project_name="test",
        run_id=run_id,
        experiment_id="test-exp",
        duration=30.0,
        emissions=emissions,
        emissions_rate=0.00001,
        cpu_power=10.0,
        gpu_power=50.0,
        ram_power=5.0,
        cpu_energy=0.0001,
        gpu_energy=0.0005,
        ram_energy=0.00005,
        energy_consumed=0.0006,
        water_consumed=0.0,
        country_name="United States",
        country_iso_code="USA",
        region="california",
        cloud_provider="Amazon",
        cloud_region="us-2",
        os="Linux",
        python_version="3.11",
        codecarbon_version="3.2.6",
        cpu_count=8,
        cpu_model="Test CPU",
        gpu_count=1,
        gpu_model="Test GPU",
        longitude=-122.0,
        latitude=37.0,
        ram_total_size=16.0,
        tracking_mode="machine",
    )


class TestFileOutputLiveOut:

    def test_live_out_creates_csv_file(self, tmp_path):
        """live_out should create the CSV file if it doesn't exist."""
        handler = FileOutput("test.csv", str(tmp_path))
        emissions = make_emissions_data()

        handler.live_out(emissions, emissions)

        assert os.path.exists(os.path.join(str(tmp_path), "test.csv"))

    def test_live_out_writes_data_to_csv(self, tmp_path):
        """live_out should write emissions data to CSV."""
        handler = FileOutput("test.csv", str(tmp_path))
        emissions = make_emissions_data(emissions=0.001)

        handler.live_out(emissions, emissions)

        df = pd.read_csv(os.path.join(str(tmp_path), "test.csv"))
        assert len(df) == 1
        assert df["emissions"].iloc[0] == pytest.approx(0.001)

    def test_live_out_append_mode_adds_rows(self, tmp_path):
        """live_out in append mode should add a new row each call."""
        handler = FileOutput("test.csv", str(tmp_path), on_csv_write="append")

        emissions1 = make_emissions_data(emissions=0.001)
        emissions2 = make_emissions_data(emissions=0.002)
        emissions3 = make_emissions_data(emissions=0.003)

        handler.live_out(emissions1, emissions1)
        handler.live_out(emissions2, emissions2)
        handler.live_out(emissions3, emissions3)

        df = pd.read_csv(os.path.join(str(tmp_path), "test.csv"))
        assert len(df) == 3

    def test_live_out_update_mode_updates_row(self, tmp_path):
        """live_out in update mode should update existing run_id row."""
        handler = FileOutput("test.csv", str(tmp_path), on_csv_write="update")
        run_id = "same-run-id"

        emissions1 = make_emissions_data(run_id=run_id, emissions=0.001)
        emissions2 = make_emissions_data(run_id=run_id, emissions=0.005)

        handler.live_out(emissions1, emissions1)
        handler.live_out(emissions2, emissions2)

        df = pd.read_csv(os.path.join(str(tmp_path), "test.csv"))
        # should only have 1 row since same run_id is updated
        assert len(df) == 1
        assert df["emissions"].iloc[0] == pytest.approx(0.005)

    def test_live_out_data_written_before_stop(self, tmp_path):
        """
        Key test for issue #448 - verifies data is written during run
        not just at the end.
        """
        handler = FileOutput("test.csv", str(tmp_path))
        emissions = make_emissions_data(emissions=0.001)

        # simulate periodic live_out calls during a run
        handler.live_out(emissions, emissions)

        # file should exist with data BEFORE stop/out is called
        csv_path = os.path.join(str(tmp_path), "test.csv")
        assert os.path.exists(csv_path), "CSV should exist after live_out call"
        df = pd.read_csv(csv_path)
        assert len(df) == 1, "CSV should have data after live_out call"

    def test_live_out_followed_by_out(self, tmp_path):
        """
        live_out during run followed by out at stop should work correctly
        in update mode - final stop should update the existing row.
        """
        handler = FileOutput("test.csv", str(tmp_path), on_csv_write="update")
        run_id = "test-run"

        # simulate periodic writes during run
        partial = make_emissions_data(run_id=run_id, emissions=0.001)
        handler.live_out(partial, partial)
        handler.live_out(partial, partial)

        # simulate final write at stop
        final = make_emissions_data(run_id=run_id, emissions=0.010)
        handler.out(final, final)

        df = pd.read_csv(os.path.join(str(tmp_path), "test.csv"))
        # should only have 1 row with final emissions value
        assert len(df) == 1
        assert df["emissions"].iloc[0] == pytest.approx(0.010)
