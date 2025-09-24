import csv
import os
import tempfile

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.file import FileOutput


def test_has_valid_headers_true_and_false():
    # Prepare headers and data
    # Use all required EmissionsData fields
    headers = [
        "timestamp",
        "project_name",
        "run_id",
        "experiment_id",
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
        "on_cloud",
        "pue",
    ]
    # All string fields
    str_fields = [
        "timestamp",
        "project_name",
        "run_id",
        "experiment_id",
        "country_name",
        "country_iso_code",
        "region",
        "cloud_provider",
        "cloud_region",
        "os",
        "python_version",
        "codecarbon_version",
        "cpu_model",
        "gpu_model",
        "tracking_mode",
        "on_cloud",
    ]
    row = {}
    for k in headers:
        if k in str_fields:
            row[k] = "foo"
        else:
            row[k] = 1.0
    data = EmissionsData(
        timestamp=row["timestamp"],
        project_name=row["project_name"],
        run_id=row["run_id"],
        experiment_id=row["experiment_id"],
        duration=row["duration"],
        emissions=row["emissions"],
        emissions_rate=row["emissions_rate"],
        cpu_power=row["cpu_power"],
        gpu_power=row["gpu_power"],
        ram_power=row["ram_power"],
        cpu_energy=row["cpu_energy"],
        gpu_energy=row["gpu_energy"],
        ram_energy=row["ram_energy"],
        energy_consumed=row["energy_consumed"],
        country_name=row["country_name"],
        country_iso_code=row["country_iso_code"],
        region=row["region"],
        cloud_provider=row["cloud_provider"],
        cloud_region=row["cloud_region"],
        os=row["os"],
        python_version=row["python_version"],
        codecarbon_version=row["codecarbon_version"],
        cpu_count=row["cpu_count"],
        cpu_model=row["cpu_model"],
        gpu_count=row["gpu_count"],
        gpu_model=row["gpu_model"],
        longitude=row["longitude"],
        latitude=row["latitude"],
        ram_total_size=row["ram_total_size"],
        tracking_mode=row["tracking_mode"],
        on_cloud=row["on_cloud"],
        pue=row["pue"],
    )
    # Create a temp directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.csv")
        # Write CSV with correct headers
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(row)
        # Create FileOutput instance
        file_output = FileOutput("test.csv", tmpdir)
        file_output.save_file_path = file_path  # ensure path
        # Should return True
        assert file_output.has_valid_headers(data) is True
        # Now write CSV with wrong headers
        wrong_headers = ["x", "y", "z"]
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=wrong_headers)
            writer.writeheader()
            writer.writerow({"x": 1, "y": 2, "z": 3})
        # Should return False
        assert file_output.has_valid_headers(data) is False

        # Now write an empty CSV file
        with open(file_path, "w", newline="") as f:
            pass
        # Should return True as there are no entries
        assert file_output.has_valid_headers(data) is True
