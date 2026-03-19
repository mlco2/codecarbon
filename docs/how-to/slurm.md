# Using CodeCarbon on SLURM (Adastra/ROCm Example)

This guide walks through using CodeCarbon on SLURM-based HPC clusters. The examples are specific to the Adastra supercomputer with AMD ROCm GPUs, but the general approach applies to any SLURM cluster with internet-connected login nodes.

**For a general approach to running CodeCarbon on any Linux server without HPC complexity, see the [Linux Service guide](linux-service.md).**

---

## Overview

This guide shows how to run CodeCarbon on SLURM-based HPC clusters like Adastra (powered by GENCI/CINES). The examples use AMD ROCm GPUs, but the approach applies to any SLURM cluster with internet-connected login nodes.

## Prerequisites

- Access to a SLURM-based HPC cluster
- Login node with internet access
- Python 3.10+ on the cluster
- Compute nodes (may be offline from internet)

## Architecture Overview

Adastra uses a standard HPC security model:

- **Login nodes** have internet access and are accessible from outside
- **Compute nodes** run your GPU workloads without direct internet access
- Python environments are set up on login nodes and shared via network storage
- Jobs are submitted from the login node using `sbatch`

For sites requiring jump hosts (bastion servers), SSH jump (`-J`) can route through an intermediate server.

The Python environment is set up on the login node and shared with compute nodes via network storage. Jobs are submitted from the login node using `sbatch`, and the SLURM script loads the environment and runs code on compute nodes.

!!! note "Debug Partition"
    If the `--time` option is less than 30 minutes, the job is placed in the `debug` partition, which has faster scheduling but shorter maximum runtime.

## Setup Steps

### Step 1: Configure Your Environment Variables

Set up environment variables for your HPC configuration. Add these to your `.bashrc` or `.zshrc`:

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

### Step 2: Connect to the HPC Cluster

Connect to your HPC login node:

**Using sshpass (automated):**

```bash
sshpass -p "$HPC_PASS" ssh -J $BASTION_USER@$BASTION_IP $USER_NAME@$HPC_HOST
```

**For first-time connection (debug SSH issues):**

```bash
ssh -o ServerAliveInterval=60 $BASTION_USER@$BASTION_IP
ssh -o ServerAliveInterval=60 $USER_NAME@$HPC_HOST
```

### Step 3: Copy Your Code to the HPC Cluster

```bash
sshpass -p "$HPC_PASS" scp -r -J $BASTION_USER@$BASTION_IP /you/folder/* $USER_NAME@$HPC_HOST:$HPC_PROJECT_FOLDER
```

### Step 4: Install CodeCarbon and Dependencies

!!! warning "ROCM Compatibility"
    Install the correct version of `amdsmi` that matches your ROCM version. For Adastra, use `amdsmi==7.0.1` for compatibility with ROCM 6.4.3.

#### Option A: Simple Installation (Recommended)


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

#### Option B: Development Installation with PyTorch

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

### Step 5: Development Workflow

For ongoing development, follow this workflow:

1. **Code locally** on your machine and push to a repository (GitHub, etc.)
2. **Pull on the login node** to avoid losing work
3. **Activate the environment** after each login:

```bash
cd codecarbon
git pull
source .venv/bin/activate
```

### Step 6: Submit a Job

Submit your CodeCarbon job to the SLURM scheduler:

Use `sbatch` to submit your job script:

```bash
sbatch examples/slurm_rocm/run_codecarbon_pytorch.slurm
```

### Step 7: Monitor Job Status

Monitor your job execution:

```bash
# View all running jobs
squeue -u $USER

# View specific job output
tail -f logs/<job_id>.out

# View job details
sinfo
```

## Troubleshooting

### Error: AMD GPU detected but amdsmi is not properly configured

```
[codecarbon WARNING @ 10:28:46] AMD GPU detected but amdsmi is not properly configured.
Error: /opt/rocm/lib/libamd_smi.so: undefined symbol: amdsmi_get_cpu_affinity_with_scope
```

**Solution:** You have a version mismatch between `amdsmi` Python package and ROCM. Install the correct version:

```bash
# For ROCM 7.0.1:
pip install amdsmi==7.0.1

# Ensure Python version matches your requirements (3.12 for Adastra)
python -V
```

### Error: KeyError 'ROCM_PATH'

This means the ROCm module is not loaded. Load it before running your job:

```bash
module load rocm/7.0.1
```

## Next Steps

- [View your emissions results](cloud-api.md) on the CodeCarbon dashboard
- [Configure CodeCarbon](configuration.md) for different measurement intervals
- [Explore other deployment options](linux-service.md) for non-HPC systems

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

