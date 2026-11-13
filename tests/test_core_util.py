import os
import shutil
import tempfile
from unittest import mock

import pytest

from codecarbon.core.util import (
    _cgroup_cpu_limit,
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
    first_file = tempfile.NamedTemporaryFile(delete=False)
    second_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        first_file.close()
        second_file.close()

        backup(first_file.name)
        expected_backup_path = resolve_path(f"{first_file.name}.bak")
        assert expected_backup_path.exists()

        # re-create file and back it up again
        shutil.copyfile(second_file.name, first_file.name)
        backup(first_file.name)
        backup_of_backup_path = resolve_path(f"{first_file.name}_0.bak")
        assert backup_of_backup_path.exists()
    finally:
        for path in [
            first_file.name,
            second_file.name,
            f"{first_file.name}.bak",
            f"{first_file.name}_0.bak",
        ]:
            resolved = resolve_path(path)
            if resolved.exists():
                resolved.unlink()


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
        with mock.patch(
            "codecarbon.core.util.os.sched_getaffinity",
            return_value={0, 1, 2, 3},
            create=True,
        ):
            with mock.patch(
                "codecarbon.core.util._cgroup_cpu_limit", return_value=None
            ):
                assert count_cpus() == 4


def test_count_cpus_respects_affinity():
    # A process pinned to a subset of the machine's cores (taskset,
    # docker --cpuset-cpus, a cpuset) must not be told there are more cores
    # than it may run on, or the CPU power estimate is inflated.
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", None):
        with mock.patch(
            "codecarbon.core.util.os.sched_getaffinity",
            return_value={0, 1},
            create=True,
        ):
            with mock.patch(
                "codecarbon.core.util._cgroup_cpu_limit", return_value=None
            ):
                assert count_cpus() == 2


def test_count_cpus_respects_cgroup_quota():
    # A cgroup CPU quota (docker --cpus, a Kubernetes CPU limit) caps CPU time
    # without restricting the affinity mask, so it must be honoured separately
    # and rounded up.
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", None):
        with mock.patch(
            "codecarbon.core.util.os.sched_getaffinity",
            return_value=set(range(8)),
            create=True,
        ):
            with mock.patch("codecarbon.core.util._cgroup_cpu_limit", return_value=2.0):
                assert count_cpus() == 2


def test_count_cpus_affinity_unavailable_falls_back():
    # Where the affinity mask cannot be read (non-Linux, or the call fails),
    # fall back to the machine's CPU count.
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", None):
        with mock.patch(
            "codecarbon.core.util.os.sched_getaffinity",
            side_effect=OSError,
            create=True,
        ):
            with mock.patch("codecarbon.core.util.psutil.cpu_count", return_value=4):
                with mock.patch(
                    "codecarbon.core.util._cgroup_cpu_limit", return_value=None
                ):
                    assert count_cpus() == 4


def test_cgroup_cpu_limit_parsing():
    # Parsing is exercised against fixture files so the test needs no root and
    # no real cgroup.
    with tempfile.TemporaryDirectory() as rootdir:
        proc = os.path.join(rootdir, "proc_cgroup")
        # cgroup v2: "<quota> <period>" in a leaf cpu.max == 1.5 CPUs
        with open(proc, "w") as f:
            f.write("0::/mygroup\n")
        leaf = os.path.join(rootdir, "mygroup")
        os.makedirs(leaf)
        with open(os.path.join(leaf, "cpu.max"), "w") as f:
            f.write("150000 100000\n")
        assert _cgroup_cpu_limit(proc, rootdir) == pytest.approx(1.5)
        # "max" means no quota -> None
        with open(os.path.join(leaf, "cpu.max"), "w") as f:
            f.write("max 100000\n")
        assert _cgroup_cpu_limit(proc, rootdir) is None
    with tempfile.TemporaryDirectory() as rootdir:
        # cgroup v1: cpu.cfs_quota_us / cpu.cfs_period_us == 2.0 CPUs
        proc = os.path.join(rootdir, "proc_cgroup")
        with open(proc, "w") as f:
            f.write("5:cpu,cpuacct:/mygroup\n")
        leaf = os.path.join(rootdir, "cpu,cpuacct", "mygroup")
        os.makedirs(leaf)
        with open(os.path.join(leaf, "cpu.cfs_quota_us"), "w") as f:
            f.write("200000\n")
        with open(os.path.join(leaf, "cpu.cfs_period_us"), "w") as f:
            f.write("100000\n")
        assert _cgroup_cpu_limit(proc, rootdir) == pytest.approx(2.0)


def test_count_cpus_slurm():
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output"
        ) as mock_subprocess_output:
            mock_subprocess_output.return_value = b"NumCPUs=8 gres/gpu=2\n"
            assert count_cpus() == 8
            # scontrol must be invoked as an argument list without a shell, so a
            # crafted SLURM_JOB_ID can never be interpreted as a shell command.
            mock_subprocess_output.assert_called_once_with(
                ["scontrol", "show", "job", "12345"]
            )
            assert mock_subprocess_output.call_args.kwargs.get("shell") is None


def test_count_cpus_slurm_job_id_is_not_shell_interpreted():
    """A SLURM_JOB_ID with shell metacharacters is passed as a single argv item,
    never expanded by a shell."""
    injection = "1; touch /tmp/pwned"
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", injection):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output"
        ) as mock_subprocess_output:
            mock_subprocess_output.return_value = b"NumCPUs=8\n"
            count_cpus()
            mock_subprocess_output.assert_called_once_with(
                ["scontrol", "show", "job", injection]
            )
            assert mock_subprocess_output.call_args.kwargs.get("shell") is None


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


def test_count_cpus_slurm_scontrol_missing():
    """SLURM env vars can be set inside a container that lacks the scontrol binary."""
    with mock.patch("codecarbon.core.util.SLURM_JOB_ID", "12345"):
        with mock.patch(
            "codecarbon.core.util.subprocess.check_output",
            side_effect=FileNotFoundError(2, "No such file or directory", "scontrol"),
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
