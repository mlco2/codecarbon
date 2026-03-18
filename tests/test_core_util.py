import shutil
import tempfile
from unittest import mock

import pytest

from codecarbon.core.util import (
    backup,
    count_cpus,
    detect_cpu_model,
    is_mac_arm,
    resolve_path,
)


def test_detect_cpu_model_caching():
    """Test that detect_cpu_model() results are cached."""
    # Clear cache to ensure clean state
    detect_cpu_model.cache_clear()

    # First call should populate cache
    result1 = detect_cpu_model()
    cache_info1 = detect_cpu_model.cache_info()
    assert cache_info1.hits == 0
    assert cache_info1.misses == 1

    # Second call should hit cache
    result2 = detect_cpu_model()
    cache_info2 = detect_cpu_model.cache_info()
    assert cache_info2.hits == 1
    assert cache_info2.misses == 1

    # Results should be identical
    assert result1 == result2

    # Third call should also hit cache
    detect_cpu_model()
    cache_info3 = detect_cpu_model.cache_info()
    assert cache_info3.hits == 2
    assert cache_info3.misses == 1


def test_backup():
    first_file = tempfile.NamedTemporaryFile()
    backup(first_file.name)
    expected_backup_path = resolve_path(f"{first_file.name}.bak")
    assert expected_backup_path.exists()
    # re-create file and back it up again
    second_file = tempfile.NamedTemporaryFile()
    shutil.copyfile(second_file.name, first_file.name)
    backup(first_file.name)
    backup_of_backup_path = resolve_path(f"{first_file.name}_0.bak")
    assert backup_of_backup_path.exists()


@pytest.mark.parametrize(
    "cpu_model, expected",
    [
        # Apple Silicon chips that should match
        ("Apple M1", True),
        ("Apple M2", True),
        ("Apple M3", True),
        ("Apple M4", True),
        ("Apple M1 Pro", True),
        ("Apple M2 Max", True),
        ("Apple M3 Ultra", True),
        ("Apple M4 Pro", True),
        ("Apple M10", True),
        # Non-Apple ARM or unrelated chips that should NOT match
        ("Intel Core i7-9750H", False),
        ("AMD Ryzen 9 5900X", False),
        ("Qualcomm Snapdragon 8cx Gen 3", False),
        # Partial matches that should NOT match (no word boundary)
        ("SuperM2000 Processor", False),
        ("M2fast chip", False),
        # Empty string
        ("", False),
    ],
)
def test_is_mac_arm(cpu_model, expected):
    assert is_mac_arm(cpu_model) == expected


def test_count_cpus_no_slurm():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", None):
        with mock.patch("codecarbon.core.util.psutil.cpu_count", return_value=4):
            assert count_cpus() == 4


def test_count_cpus_slurm():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output"
        ) as mock_subprocess_output:
            mock_subprocess_output.return_value = b"NumCPUs=8 gres/gpu=2\n"
            assert count_cpus() == 8


def test_count_cpus_slurm_no_gpu():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output"
        ) as mock_subprocess_output:
            mock_subprocess_output.return_value = b"NumCPUs=16\n"
            assert count_cpus() == 16


def test_count_cpus_slurm_exception():
    import subprocess

    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "cmd"),
        ):
            with mock.patch("codecarbon.core.util.psutil.cpu_count", return_value=4):
                assert count_cpus() == 4


def test_count_cpus_slurm_malformed():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output",
            return_value=b"Something Else\n",
        ):
            with mock.patch("codecarbon.core.util.psutil.cpu_count", return_value=4):
                assert count_cpus() == 4


def test_count_cpus_slurm_too_many_matches():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output",
            return_value=b"NumCPUs=8 NumCPUs=16\n",
        ):
            with mock.patch("codecarbon.core.util.psutil.cpu_count", return_value=4):
                assert count_cpus() == 4
