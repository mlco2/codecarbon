#!/bin/bash
#SBATCH --account=cad15147
#SBATCH --constraint=MI250
#SBATCH --nodes=1
#SBATCH --time=0:25:00
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --threads-per-core=1
#SBATCH --job-name=codecarbon-test
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

# Load AMD ROCM environment
module purge
module load cpe/24.07
module load python/3.12
module load rocm/7.0.1

# Print environment info
echo "=== Job Environment ==="
echo "Running on host: $(hostname)"
echo "at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Number of GPUs: $SLURM_GPUS_PER_NODE"
echo "ROCR_VISIBLE_DEVICES: $ROCR_VISIBLE_DEVICES"
echo "HSA_OVERRIDE_GFX_VERSION: $HSA_OVERRIDE_GFX_VERSION"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "PATH: $PATH"
export PYTHONPATH=/opt/rocm-7.0.1/share/amd_smi:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

rocm-smi
rocm-smi --version
rocm-smi --showmetrics --json


# Create logs directory if it doesn't exist
mkdir -p logs

# Run the Python script
pip install amdsmi==7.0.1
echo "=== Installed AMD SMI Python Package ==="
python3 -m pip list | grep -E "(amd)"
echo "=== AMD SMI Metrics ==="
amd-smi -h
# Verify activation (optional)
echo "=== Python Version ==="
which python3
python3 --version
ls /opt/rocm-7.0.1/share/amd_smi
echo "=== ls /opt ==="
ls /opt
echo "=== Running Training Script ==="
srun python amdsmi_demo.py
