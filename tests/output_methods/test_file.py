import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData
from codecarbon.output_methods.file import FileOutput


class TestFileOutput(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test_project",
            run_id="test_run_id",
            experiment_id="test_experiment_id",
            duration=10,
            emissions=0.5,
            emissions_rate=0.05,
            cpu_power=20,
            gpu_power=30,
            ram_power=5,
            cpu_energy=200,
            gpu_energy=300,
            ram_energy=50,
            energy_consumed=550,
            water_consumed=0.1,
            country_name="Testland",
            country_iso_code="TS",
            region="Test Region",
            cloud_provider="Test Cloud",
            cloud_region="test-cloud-1",
            os="TestOS",
            python_version="3.8",
            codecarbon_version="2.0",
            cpu_count=4,
            cpu_model="Test CPU",
            gpu_count=1,
            gpu_model="Test GPU",
            longitude=0,
            latitude=0,
            ram_total_size=16,
            tracking_mode="machine",
            on_cloud="true",
            pue=1.5,
            wue=0.5,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_file_output_initialization(self):
        FileOutput("test.csv", self.temp_dir)

    def test_file_output_initialization_invalid_csv_write_mode(self):
        with self.assertRaises(ValueError):
            FileOutput("test.csv", self.temp_dir, on_csv_write="invalid_option")

    def test_file_output_initialization_invalid_dir(self):
        with self.assertRaises(OSError):
            FileOutput("test.csv", "/non/existent/dir")

    def test_has_valid_headers_success(self):
        file_output = FileOutput("test.csv", self.temp_dir)
        file_output.out(self.emissions_data, None)

        self.assertTrue(file_output.has_valid_headers(self.emissions_data))

    def test_has_valid_headers_success_with_empty_file(self):
        file_output = FileOutput("test.csv", self.temp_dir)
        with open(file_output.save_file_path, "w", newline="") as _:
            pass

        self.assertTrue(file_output.has_valid_headers(self.emissions_data))

    def test_has_valid_headers_different_order_success(self):
        file_output = FileOutput("test.csv", self.temp_dir)
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        df = df[list(reversed(df.columns))]
        df.to_csv(os.path.join(self.temp_dir, "test.csv"), index=False)

        self.assertTrue(file_output.has_valid_headers(self.emissions_data))

    def test_has_valid_headers_failure(self):
        file_output = FileOutput("test.csv", self.temp_dir)
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        df.rename(columns={"wue": "new_header"}, inplace=True)
        df.to_csv(os.path.join(self.temp_dir, "test.csv"), index=False)

        self.assertFalse(file_output.has_valid_headers(self.emissions_data))

    @patch("codecarbon.output_methods.file.FileOutput.has_valid_headers")
    def test_file_output_out_file_exists_invalid_headers(self, mock_has_valid_headers):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")
        file_output.out(self.emissions_data, None)

        mock_has_valid_headers.return_value = False
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv.bak"))
        self.assertEqual(len(df), 1)
        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 1)

    def test_file_output_out_update_no_file_exists(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="update")
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 1)

    def test_file_output_out_append_no_file_exists(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 1)

    def test_file_output_out_append_file_exists(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")
        file_output.out(self.emissions_data, None)
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 2)

    def test_file_output_out_update_file_exists_no_matching_row(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="update")
        file_output.out(self.emissions_data, None)

        updated_emissions_data = self.emissions_data
        updated_emissions_data.run_id = "new_test_run_id"
        file_output.out(updated_emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 2)

    def test_file_output_out_update_file_exists_multiple_matching_rows(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="update")
        file_output.out(self.emissions_data, None)

        # Manually add a duplicate row to simulate the condition
        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        df = pd.concat([df, df])
        df.to_csv(os.path.join(self.temp_dir, "test.csv"), index=False)

        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 3)

    def test_file_output_out_update_file_exists_one_matchingrows(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="update")
        file_output.out(self.emissions_data, None)
        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(df["cpu_power"].iloc[0], 20)

        new_data = self.emissions_data
        new_data.cpu_power = 2
        file_output.out(new_data, None)
        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(df["cpu_power"].iloc[0], 2)

    # def test_file_output_out_consistent_column_ordering(self):
    #     file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")
    #     file_output.out(self.emissions_data, None)

    def test_file_output_out_append_empty_file_exists(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")
        # Create an empty file
        with open(file_output.save_file_path, "w") as _:
            pass

        # This should not raise an error
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 1)

    def test_file_output_out_update_empty_file_exists(self):
        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="update")
        # Create an empty file
        with open(file_output.save_file_path, "w") as _:
            pass

        # This should not raise an error
        file_output.out(self.emissions_data, None)

        df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
        self.assertEqual(len(df), 1)

    def test_file_output_out_append_no_gpu_consistent_columns(self):
        """Regression test: successive appends with gpu_count=None/gpu_model=None must
        never trigger a format-change warning or produce a .bak backup file.

        The bug: dropna(axis=1, how="all") was applied to the *existing* CSV DataFrame
        as well as to new_df.  On a CPU-only machine both gpu_count and gpu_model are
        NaN in every row, so after the second write those columns were silently dropped.
        The third write then detected a schema mismatch and backed up the file.
        """
        no_gpu_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test_project",
            run_id="test_run_id",
            experiment_id="test_experiment_id",
            duration=10,
            emissions=0.5,
            emissions_rate=0.05,
            cpu_power=20,
            gpu_power=0,
            ram_power=5,
            cpu_energy=200,
            gpu_energy=0,
            ram_energy=50,
            energy_consumed=250,
            water_consumed=0.1,
            country_name="Testland",
            country_iso_code="TS",
            region="Test Region",
            cloud_provider="",
            cloud_region="",
            os="TestOS",
            python_version="3.8",
            codecarbon_version="2.0",
            cpu_count=4,
            cpu_model="Test CPU",
            gpu_count=None,
            gpu_model=None,
            longitude=0,
            latitude=0,
            ram_total_size=16,
            tracking_mode="machine",
        )

        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")

        # Write four times — prior to the fix, the 3rd write triggered a backup.
        for _ in range(4):
            file_output.out(no_gpu_data, None)
            self.assertTrue(
                file_output.has_valid_headers(no_gpu_data),
                "CSV headers became invalid after an append (gpu_count/gpu_model "
                "columns were dropped by dropna).",
            )

        # No .bak file should have been created.
        bak_path = file_output.save_file_path + ".bak"
        self.assertFalse(
            os.path.exists(bak_path),
            "A backup file was created even though the CSV schema did not change.",
        )

        # All four rows must be present.
        df = pd.read_csv(file_output.save_file_path)
        self.assertEqual(len(df), 4)

        # gpu_count and gpu_model columns must still be present (as NaN).
        self.assertIn("gpu_count", df.columns)
        self.assertIn("gpu_model", df.columns)

    def test_file_output_out_append_no_gpu_zero_defaults(self):
        """Test that gpu_count=0 and gpu_model="" (the new tracker defaults for
        CPU-only machines) produce consistent CSV columns across successive writes.
        """
        no_gpu_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test_project",
            run_id="test_run_id",
            experiment_id="test_experiment_id",
            duration=10,
            emissions=0.5,
            emissions_rate=0.05,
            cpu_power=20,
            gpu_power=0,
            ram_power=5,
            cpu_energy=200,
            gpu_energy=0,
            ram_energy=50,
            energy_consumed=250,
            water_consumed=0.1,
            country_name="Testland",
            country_iso_code="TS",
            region="Test Region",
            cloud_provider="",
            cloud_region="",
            os="TestOS",
            python_version="3.8",
            codecarbon_version="2.0",
            cpu_count=4,
            cpu_model="Test CPU",
            gpu_count=0,
            gpu_model="",
            longitude=0,
            latitude=0,
            ram_total_size=16,
            tracking_mode="machine",
        )

        file_output = FileOutput("test.csv", self.temp_dir, on_csv_write="append")

        for _ in range(4):
            file_output.out(no_gpu_data, None)
            self.assertTrue(
                file_output.has_valid_headers(no_gpu_data),
                "CSV headers should remain consistent with gpu_count=0 / gpu_model=''.",
            )

        bak_path = file_output.save_file_path + ".bak"
        self.assertFalse(
            os.path.exists(bak_path),
            "No backup should be created when columns are consistent.",
        )

        df = pd.read_csv(file_output.save_file_path)
        self.assertEqual(len(df), 4)
        self.assertIn("gpu_count", df.columns)
        self.assertIn("gpu_model", df.columns)
        # With 0/"" defaults, gpu_count should be 0 (not NaN)
        self.assertTrue((df["gpu_count"] == 0).all())
        # gpu_model="" is read back as NaN by pandas (empty string in CSV),
        # but the column must still be present.
        self.assertIn("gpu_model", df.columns)

    def test_file_output_task_out(self):
        task_emissions_data = [
            TaskEmissionsData(
                task_name="test_task",
                timestamp="2023-01-01T00:00:00",
                project_name="test_project",
                run_id="test_run_id",
                duration=10,
                emissions=0.5,
                emissions_rate=0.05,
                cpu_power=20,
                gpu_power=30,
                ram_power=5,
                cpu_energy=200,
                gpu_energy=300,
                ram_energy=50,
                energy_consumed=550,
                water_consumed=0.1,
                country_name="Testland",
                country_iso_code="TS",
                region="Test Region",
                cloud_provider="Test Cloud",
                cloud_region="test-cloud-1",
                os="TestOS",
                python_version="3.8",
                codecarbon_version="2.0",
                cpu_count=4,
                cpu_model="Test CPU",
                gpu_count=1,
                gpu_model="Test GPU",
                longitude=0,
                latitude=0,
                ram_total_size=16,
                tracking_mode="machine",
                on_cloud="true",
            )
        ]
        file_output = FileOutput("test.csv", self.temp_dir)
        file_output.task_out(task_emissions_data, "test_experiment")

        expected_file = os.path.join(
            self.temp_dir, "emissions_test_experiment_test_run_id.csv"
        )
        self.assertTrue(os.path.exists(expected_file))
        df = pd.read_csv(expected_file)
        self.assertEqual(len(df), 1)
