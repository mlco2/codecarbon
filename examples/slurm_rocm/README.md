# CodeCarbon on CINES Adastra HPC with AMD ROCM

This project was provided with computing and storage resources by GENCI at CINES thanks to the grant AD010615147R1 on the supercomputer Adastra's MI250x/MI300 partition.

Thanks to this grant we were able to develop and test the AMD ROCM support in CodeCarbon, and provide this quick start guide to help other users of Adastra HPC to easily monitor the carbon emissions of their machine learning workloads running on AMD GPUs.

It was tested on Adastra but it will likely work on any SLURM cluster with AMD GPUs and ROCM support.

## Quick Start Guide

Adastra security rules require users to connect through a fixed IP. We choose to setup a small host in the cloud to act as a bastion server, allowing us to connect to Adastra from anywhere without needing to change our IP address.

Adastra architecture is quite standard for a HPC cluster, with a login node and compute nodes. The login node has internet access and is the only one accessible from outside, while the compute nodes are where the GPU workloads run, without internet access.

The Python environment is setup on the login node, and referenced by the compute nodes.

The job is submitted from the login node using `sbatch`, and the SLURM script takes care of loading the Python environment and running the code on the compute node.

If the `--time` option of `sbatch` is less than 30 minutes, the job will be put in the `debug` partition, which has a faster scheduling but a shorter maximum runtime.

### Export your configuration

Adapt the following environment variables with your own configuration. You can add them to your `.bashrc` or `.zshrc` for convenience.

```bash
export BASTION_IP="xx.xx.xx.xx"
export BASTION_USER="username"
export HPC_HOST="xx.xx.fr"
export HPC_PASS="xxxxx"
export PROJECT_ID="xxx"
export USER_NAME="username_hpc"
export HPC_PROJECT_FOLDER="/lus/home/xxx"
```

### Connect to CINES Adastra

```bash
sshpass -p "$HPC_PASS" ssh -J $BASTION_USER@$BASTION_IP $USER_NAME@$HPC_HOST
```

For the first time you may want to connect one-by-one to debug any SSH issue before using `sshpass`:

```bash
ssh -o ServerAliveInterval=60 $BASTION_USER@$BASTION_IP
ssh -o ServerAliveInterval=60 $USER_NAME@$HPC_HOST
```

### Copy your code to Adastra

```bash
sshpass -p "$HPC_PASS" scp -r -J $BASTION_USER@$BASTION_IP /you/folder/* $USER_NAME@$HPC_HOST:$HPC_PROJECT_FOLDER
```

### Install CodeCarbon and dependencies

Be careful to install the correct version of `amdsmi` that is compatible with the ROCM version on Adastra. The last available version we used is `7.0.1`.

#### Simple installation


```bash
module load python/3.12
module load rocm/7.0.1

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Important: Adastra's MI250 runs ROCm 6.4.3 natively.
# With export ROCM_PATH=/opt/rocm-6.4.3 in our SLURM script, this python wheel perfectly matches the C library without symlink issues!
pip install amdsmi==7.0.1
pip install codecarbon
```

#### use a branch of CodeCarbon with PyTorch

```bash
module load python/3.12
module load rocm/7.0.1
git clone https://github.com/mlco2/codecarbon.git
# If you want a specific version, use git checkout <tag> to switch to the desired version.
git checkout -b feat/rocm
cd codecarbon
python -m venv .venv
source .venv/bin/activate
python -V
# Must be 3.12.x
pip install --upgrade pip
# Important: Adastra's MI250 runs ROCm 6.4.3 natively.
# With export ROCM_PATH=/opt/rocm-6.4.3 in our SLURM script, this python wheel perfectly matches the C library without symlink issues!
pip install amdsmi==7.0.1
# Look at https://download.pytorch.org/whl/torch/ for the correct version matching your Python (cp312) and ROCM version.
# torch-2.10.0+rocm7.0-cp312-cp312-manylinux_2_28_x86_64.whl
pip3 install torch==2.10.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.0
pip install numpy

# Install CodeCarbon in editable mode to allow for live code changes without reinstallation
pip install -e .
```

### Submit a Job

**Option A: Using sbatch (recommended)**
```bash
sbatch examples/slurm_rocm/run_codecarbon_pytorch.slurm
```

### 4. Monitor Job Status
```bash
# View running jobs
squeue -u $USER

# View job output
tail -f logs/<job_id>.out
```

## Troubleshooting


```
Error :
[codecarbon WARNING @ 10:28:46] AMD GPU detected but amdsmi is not properly configured. Please ensure amdsmi is correctly installed to get GPU metrics.Tips : check consistency between Python amdsmi package and ROCm versions, and ensure AMD drivers are up to date. Error: /opt/rocm/lib/libamd_smi.so: undefined symbol: amdsmi_get_cpu_affinity_with_scope
```

This mean you have a mismatch between the `amdsmi` Python package and the ROCM version installed on Adastra. To fix this, ensure you install the correct version of `amdsmi` that matches the ROCM version (e.g., `amdsmi==7.0.1` for ROCM 7.0.1).

```bash
KeyError: 'ROCM_PATH'
```
This means the rocm module is not loaded, load it with `module load rocm/7.0.1`.

## Limitations and Future Work

The AMD Instinct MI250 accelerator card contains two Graphics Compute Dies (GCDs) per physical card. However, when monitoring energy consumption (e.g., via rocm-smi or tools like CodeCarbon), only one GCD reports power usage, while the other shows zero values. This is problematic for accurate energy accounting, especially in HPC/SLURM environments where jobs may be allocated a single GCD.

So in that case we display a warning.

In a future work we will use `average_gfx_activity` to estimate the corresponding power of both GCDs, and provide an estimation instead of 0.

## Documentation

- [CINES Adastra GPU allocation](https://dci.dci-gitlab.cines.fr/webextranet/user_support/index.html#allocating-a-single-gpu)
- [CINES PyTorch on ROCM](https://dci.dci-gitlab.cines.fr/webextranet/software_stack/libraries/index.html#pytorch)
- [AMD SMI library](https://rocm.docs.amd.com/projects/amdsmi/en/latest/reference/amdsmi-py-api.html)


## Annex: Example of Job Details with scontrol

This trace was obtained to adapt `codecarbon/core/util.py` to properly parse the SLURM job details and extract the relevant information about GPU and CPU allocation. 

```
[$PROJECT_ID] $USER_NAME@login5:~/codecarbon$ scontrol show job  4687018
JobId=4687018 JobName=codecarbon-test
   UserId=$USER_NAME(xxx) GroupId=grp_$USER_NAME(xxx) MCS_label=N/A
   Priority=900000 Nice=0 Account=xxxxxx QOS=debug
   JobState=COMPLETED Reason=None Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=00:00:24 TimeLimit=00:05:00 TimeMin=N/A
   SubmitTime=2026-03-02T17:12:49 EligibleTime=2026-03-02T17:12:49
   AccrueTime=2026-03-02T17:12:49
   StartTime=2026-03-02T17:12:49 EndTime=2026-03-02T17:13:13 Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2026-03-02T17:12:49 Scheduler=Main
   Partition=mi250-shared AllocNode:Sid=login5:2553535
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=g1341
   BatchHost=g1341
   NumNodes=1 NumCPUs=16 NumTasks=1 CPUs/Task=8 ReqB:S:C:T=0:0:*:1
   ReqTRES=cpu=8,mem=29000M,node=1,billing=8,gres/gpu=1
   AllocTRES=cpu=16,mem=29000M,energy=10211,node=1,billing=16,gres/gpu=1,gres/gpu:mi250x=1
   Socks/Node=* NtasksPerN:B:S:C=1:0:*:1 CoreSpec=*
   MinCPUsNode=8 MinMemoryNode=29000M MinTmpDiskNode=0
   Features=MI250&DEBUG DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/lus/home/CT6/$PROJECT_ID/$USER_NAME/codecarbon/run_codecarbon.sh
   WorkDir=/lus/home/CT6/$PROJECT_ID/$USER_NAME/codecarbon
   AdminComment=Accounting=1 
   StdErr=/lus/home/CT6/$PROJECT_ID/$USER_NAME/codecarbon/logs/4687018.err
   StdIn=/dev/null
   StdOut=/lus/home/CT6/$PROJECT_ID/$USER_NAME/codecarbon/logs/4687018.out
   TresPerNode=gres/gpu:1
   TresPerTask=cpu=8
```

