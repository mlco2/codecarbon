import unittest

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
                n_gb_W = (new_W - ref_W) / ram.power_per_GB
                is_close = np.isclose(n_gb, n_gb_W, atol=1e-3)
                self.assertTrue(
                    is_close,
                    msg=f"{array_size}, {n_gb}, {n_gb_W}, {is_close}",
                )
                del array

    def test_ram_slurm(self):
        scontrol_str = """
scontrol show job $SLURM_JOBID
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
        ram = RAM(tracking_mode="slurm")
        ram_size = ram._parse_scontrol(scontrol_str)
        self.assertEqual(ram_size, "128G")
        scontrol_str = """
   ReqTRES=cpu=32,mem=134G,node=1,billing=40,gres/gpu=4
   AllocTRES=cpu=64,mem=42K,node=1,billing=40,gres/gpu=4
   """
        ram = RAM(tracking_mode="slurm")
        ram_size = ram._parse_scontrol(scontrol_str)
        self.assertEqual(ram_size, "42K")
