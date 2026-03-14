import shutil
import tempfile
from unittest import mock

from codecarbon.core.util import backup, count_cpus, detect_cpu_model, resolve_path


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
