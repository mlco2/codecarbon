import unittest
from textwrap import dedent
from unittest import mock

import numpy as np

from codecarbon.external.hardware import RAM

# TODO: need help: test multiprocess case


class TestRAM(unittest.TestCase):
    def test_ram_diff(self):
        ram = RAM(tracking_mode="process")

        for array_size in [
            # (10, 10),  # too small to be noticed
            # (100, 100),  # too small to be noticed
            (1000, 1000),  # ref for atol
            (10, 1000, 1000),
            (20, 1000, 1000),
            (100, 1000, 1000),
            (200, 1000, 1000),
            (1000, 1000, 1000),
            (2000, 1000, 1000),
        ]:
            with self.subTest(array_size=array_size):
                ref_W = ram.total_power().W
                array = np.ones(array_size, dtype=np.int8)
                new_W = ram.total_power().W
                n_gb = array.nbytes / (1024**3)
                # For backward compatibility, calculate an effective power_per_GB
                memory_gb = ram.process_memory_GB
                ram_power = ram._calculate_ram_power(memory_gb)
                # Calculate an effective power per GB for comparison
                ram.power_per_GB = ram_power / memory_gb if memory_gb > 0 else 0
                n_gb_W = (new_W - ref_W) / ram.power_per_GB
                is_close = np.isclose(n_gb, n_gb_W, atol=1e-3)
                self.assertTrue(
                    is_close,
                    msg=f"{array_size}, {n_gb}, {n_gb_W}, {is_close}",
                )
                del array

    def test_ram_slurm(self):
        scontrol_str = dedent(
            """\
            scontrol show job $SLURM_JOB_ID
            JobId=XXXX JobName=gpu-jupyterhub
               UserId=XXXX GroupId=XXXX MCS_label=N/A
               Priority=255342 Nice=0 Account=puk@v100 QOS=qos_gpu-t3
               JobState=RUNNING Reason=None Dependency=(null)
               Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
               RunTime=00:33:42 TimeLimit=08:00:00 TimeMin=N/A
               SubmitTime=2023-10-23T10:45:25 EligibleTime=2023-10-23T10:45:25
               AccrueTime=2023-10-23T10:45:25
               StartTime=2023-10-23T10:45:35 EndTime=2023-10-23T18:45:35 Deadline=N/A
               SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-10-23T10:45:35 Scheduler=Main
               Partition=gpu_p13 AllocNode:Sid=idrsrv12-ib0:500994
               ReqNodeList=(null) ExcNodeList=(null)
               NodeList=r13i5n0
               BatchHost=r13i5n0
               NumNodes=1 NumCPUs=64 NumTasks=1 CPUs/Task=32 ReqB:S:C:T=0:0:*:1
               ReqTRES=cpu=32,mem=128G,node=1,billing=40,gres/gpu=4
               AllocTRES=cpu=64,mem=128G,node=1,billing=40,gres/gpu=4
               Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
               MinCPUsNode=32 MinMemoryCPU=4G MinTmpDiskNode=0
               Features=v100-16g DelayBoot=00:00:00
               OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
               Command=(null)
               WorkDir=/linkhome/rech/gendxh01/uei48xr
               StdErr=/linkhome/rech/gendxh01/uei48xr/jupyterhub_slurm.err
               StdIn=/dev/null
               StdOut=/linkhome/rech/gendxh01/uei48xr/jupyterhub_slurm.out
               Power=
               TresPerNode=gres:gpu:4
            """
        )
        ram = RAM(tracking_mode="slurm")
        ram_size = ram._parse_scontrol(scontrol_str)
        self.assertEqual(ram_size, "128G")
        scontrol_str = dedent(
            """\
            ReqTRES=cpu=32,mem=134G,node=1,billing=40,gres/gpu=4
            AllocTRES=cpu=64,mem=42K,node=1,billing=40,gres/gpu=4
            """
        )
        ram = RAM(tracking_mode="slurm")
        ram_size = ram._parse_scontrol(scontrol_str)
        self.assertEqual(ram_size, "42K")

        scontrol_str = dedent(
            """\
            TRES=cpu=64,mem=50000M,node=1,billing=40,gres/gpu=4
            """
        )
        ram = RAM(tracking_mode="slurm")
        ram_size = ram._parse_scontrol(scontrol_str)
        self.assertEqual(ram_size, "50000M")

    def test_detect_arm_cpu(self):
        """Test ARM CPU detection logic"""
        # Mock platform.machine to return ARM architecture
        with mock.patch("platform.machine", return_value="aarch64"):
            ram = RAM(tracking_mode="machine")
            self.assertTrue(ram.is_arm_cpu)

        # Mock platform.machine to return x86 architecture
        with mock.patch("platform.machine", return_value="x86_64"):
            ram = RAM(tracking_mode="machine")
            self.assertFalse(ram.is_arm_cpu)

        # Test exception handling
        with mock.patch("platform.machine", side_effect=Exception("Mock exception")):
            ram = RAM(tracking_mode="machine")
            self.assertFalse(ram.is_arm_cpu)  # Should default to False on error

    def test_estimate_dimm_count(self):
        """Test DIMM count estimation based on RAM size"""
        ram = RAM(tracking_mode="machine")

        # Test very small RAM systems (embedded/IoT)
        self.assertEqual(ram._estimate_dimm_count(1), 1)
        self.assertEqual(ram._estimate_dimm_count(2), 1)

        # Test standard desktop/laptop configurations
        self.assertEqual(
            ram._estimate_dimm_count(4), 2
        )  # Min 2 DIMMs for small systems
        self.assertEqual(ram._estimate_dimm_count(8), 2)  # Likely 2 DIMMs of 4GB
        self.assertEqual(ram._estimate_dimm_count(16), 3)  # Likely 2x8GB or 4x4GB
        self.assertEqual(ram._estimate_dimm_count(32), 4)  # Likely 4x8GB or 2x16GB

        # Test workstation/small server configurations
        self.assertEqual(ram._estimate_dimm_count(64), 4)  # Likely 4x16GB
        self.assertEqual(ram._estimate_dimm_count(96), 6)  # Likely 6x16GB
        self.assertEqual(ram._estimate_dimm_count(128), 8)  # Likely 8x16GB or 4x32GB

        # Test large server configurations
        self.assertEqual(ram._estimate_dimm_count(256), 8)  # Likely 8x32GB
        self.assertEqual(ram._estimate_dimm_count(512), 8)  # Likely 8x64GB
        self.assertEqual(ram._estimate_dimm_count(1024), 8)  # Likely 8x128GB

        # Test very large server configurations (should cap at reasonable DIMM counts)
        self.assertEqual(ram._estimate_dimm_count(2048), 16)  # Likely 16x128GB
        self.assertEqual(ram._estimate_dimm_count(4096), 32)  # Likely 32x128GB
        self.assertEqual(ram._estimate_dimm_count(8192), 32)  # Capped at 32 DIMMs

    def test_calculate_ram_power(self):
        """Test RAM power calculation with different system configurations"""
        # Test x86 system
        with mock.patch.object(RAM, "_detect_arm_cpu", return_value=False):
            ram = RAM(tracking_mode="machine")

            # Test minimum power enforcement (should be 5W for x86)
            self.assertEqual(
                ram._calculate_ram_power(1), 5.0
            )  # Should enforce minimum 5W

            # Standard laptop/desktop
            self.assertEqual(ram._calculate_ram_power(8), 5.0)  # 2 DIMMs at 2.5W = 5W
            self.assertEqual(
                ram._calculate_ram_power(16), 7.5
            )  # 3 DIMMs at 2.5W = 7.5W

            # Small server
            power_32gb = ram._calculate_ram_power(32)
            self.assertEqual(power_32gb, 10.0)  # 4 DIMMs at 2.5W = 10W

            # Medium server with diminishing returns
            power_128gb = ram._calculate_ram_power(128)
            expected_128gb = (4 * 2.5) + (
                4 * 2.5 * 0.9
            )  # First 4 DIMMs at full power, next 4 at 90%
            self.assertAlmostEqual(power_128gb, expected_128gb, places=2)

            # Large server with more diminishing returns
            power_1024gb = ram._calculate_ram_power(1024)
            # Complex calculation with tiered efficiency
            expected_1024gb = (4 * 2.5) + (4 * 2.5 * 0.9) + (8 * 2.5 * 0.8)
            self.assertAlmostEqual(power_1024gb, expected_1024gb, places=2)

            # Very large server should have significant efficiency gains
            power_4096gb = ram._calculate_ram_power(4096)
            # Should cap at 32 DIMMs with efficiency tiers
            expected_4096gb = (
                (4 * 2.5) + (4 * 2.5 * 0.9) + (8 * 2.5 * 0.8) + (16 * 2.5 * 0.7)
            )
            self.assertAlmostEqual(power_4096gb, expected_4096gb, places=2)

        # Test ARM system
        with mock.patch.object(RAM, "_detect_arm_cpu", return_value=True):
            ram = RAM(tracking_mode="machine")

            # Test minimum power enforcement (should be 3W for ARM)
            self.assertEqual(
                ram._calculate_ram_power(1), 3.0
            )  # Should enforce minimum 3W

            # Standard ARM system
            self.assertEqual(ram._calculate_ram_power(4), 3.0)  # 2 DIMMs at 1.5W = 3W

            # ARM server (less common but possible)
            power_16gb_arm = ram._calculate_ram_power(16)
            expected_16gb_arm = 3 * 1.5  # 3 DIMMs at 1.5W
            self.assertAlmostEqual(power_16gb_arm, expected_16gb_arm, places=2)

            # Larger ARM server should still be more power efficient
            power_64gb_arm = ram._calculate_ram_power(64)
            expected_64gb_arm = (4 * 1.5) + (0.9 * 1.5 * 0)  # 4 DIMMs at full power
            self.assertAlmostEqual(power_64gb_arm, expected_64gb_arm, places=2)

    def test_power_calculation_consistency(self):
        """Test that the power calculation is consistent with expected scaling behavior"""
        ram = RAM(tracking_mode="machine")

        # Power should increase with memory size but at a diminishing rate
        power_8gb = ram._calculate_ram_power(8)
        power_16gb = ram._calculate_ram_power(16)
        power_32gb = ram._calculate_ram_power(32)
        power_64gb = ram._calculate_ram_power(64)
        power_128gb = ram._calculate_ram_power(128)
        power_256gb = ram._calculate_ram_power(256)
        power_1024gb = ram._calculate_ram_power(1024)

        # Power should increase with memory
        self.assertLess(power_8gb, power_16gb)
        self.assertLess(power_16gb, power_32gb)
        self.assertLess(power_32gb, power_64gb)

        # The rate of increase should diminish
        diff_8_16 = power_16gb - power_8gb
        diff_16_32 = power_32gb - power_16gb
        power_64gb - power_32gb
        diff_64_128 = power_128gb - power_64gb
        diff_128_256 = power_256gb - power_128gb
        diff_256_1024 = power_1024gb - power_256gb

        # Each doubling of memory should add less power than the previous doubling
        watts_per_gb_8_16 = diff_8_16 / 8  # power added per additional GB from 8 to 16
        watts_per_gb_16_32 = (
            diff_16_32 / 16
        )  # power added per additional GB from 16 to 32
        self.assertGreaterEqual(watts_per_gb_8_16, watts_per_gb_16_32)

        # For large memory sizes, the power increase should be even smaller per GB
        watts_per_gb_64_128 = diff_64_128 / 64
        watts_per_gb_128_256 = diff_128_256 / 128
        watts_per_gb_256_1024 = diff_256_1024 / 768
        self.assertGreaterEqual(watts_per_gb_64_128, watts_per_gb_128_256)
        self.assertGreaterEqual(watts_per_gb_128_256, watts_per_gb_256_1024)
