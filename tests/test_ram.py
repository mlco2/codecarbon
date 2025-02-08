import unittest
from textwrap import dedent
from time import sleep
from unittest import mock

import numpy as np

from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.external.hardware import RAM

# TODO: need help: test multiprocess case


@mock.patch("psutil.virtual_memory")
class TestRAM(unittest.TestCase):
    def setUp(self):
        # Mock memory size to 32GB for consistent testing
        self.total_memory = 32 * 1024 * 1024 * 1024  # 32GB in bytes

    def test_ram_diff(self, mock_virtual_memory):
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
                n_gb_W = (new_W - ref_W) / ram.power_per_GB
                is_close = np.isclose(n_gb, n_gb_W, atol=1e-3)
                self.assertTrue(
                    is_close,
                    msg=f"{array_size}, {n_gb}, {n_gb_W}, {is_close}",
                )
                del array

    def test_ram_slurm(self, mock_virtual_memory):
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

    def test_ram_total_power(self, mock_virtual_memory):
        # Setup mock to return 50% RAM usage on 32GB system
        mock_virtual_memory.return_value = mock.Mock(
            total=self.total_memory,  # 32GB
            percent=50.0,  # 50% usage
        )

        ram = RAM(tracking_mode="machine")
        ram.start()
        sleep(0.5)
        power = ram._get_power_from_ram_load()
        # Expected: (32/8) * 3.0 * 0.5 = 6.0W for 50% of 32GB
        self.assertEqual(power.W, 6.0)
        self.assertEqual(ram.total_power().W, 12)  # 32 * 3.0/8  = 12.0W

    def test_ram_load_detection(self, mock_virtual_memory):
        # Setup mock to return 100% RAM usage on 32GB system
        mock_virtual_memory.return_value = mock.Mock(total=self.total_memory, percent=100.0)

        tracker = OfflineEmissionsTracker(country_iso_code="FRA")
        for hardware in tracker._hardware:
            if isinstance(hardware, RAM):
                break
        else:
            raise Exception("No RAM tracking found!")

        tracker.start()
        sleep(0.5)
        emission = tracker.stop()
        self.assertGreater(emission, 0.0)

    def test_ram_power_calculation_at_different_loads(self, mock_virtual_memory):
        ram = RAM(tracking_mode="machine")
        # Mock machine_memory_GB to return 32
        with mock.patch.object(RAM, "machine_memory_GB", new_callable=mock.PropertyMock) as mock_mem:
            mock_mem.return_value = 32
            tests_values = [
                {
                    "ram_load": 0.0,
                    "expected_power": 0.0,
                },
                {
                    "ram_load": 50.0,
                    "expected_power": 6.0,  # 32 * 3.0/8 * 0.5 = 6.0W
                },
                {
                    "ram_load": 100.0,
                    "expected_power": 12.0,  # 32  * 3.0/8 * 1.0 = 12.0W
                },
            ]

            for test in tests_values:
                mock_virtual_memory.return_value = mock.Mock(total=self.total_memory, percent=test["ram_load"])
                power = ram._get_power_from_ram_load()
                self.assertEqual(power.W, test["expected_power"])

    def test_ram_power_different_sizes(self, mock_virtual_memory):
        test_sizes = [
            (8, 3.0),  # 8GB should use 3.0W at 100%
            (16, 6.0),  # 16GB should use 6.0W at 100%
            (32, 12.0),  # 32GB should use 12.0W at 100%
            (64, 24.0),  # 64GB should use 24.0W at 100%
        ]

        for gb_size, expected_power in test_sizes:
            mock_virtual_memory.return_value = mock.Mock(
                total=gb_size * 1024 * 1024 * 1024,  # Convert GB to bytes
                percent=100.0,  # 100% usage
            )
            ram = RAM(tracking_mode="machine")
            power = ram._get_power_from_ram_load()
            self.assertEqual(power.W, expected_power, f"Failed for {gb_size}GB RAM")
