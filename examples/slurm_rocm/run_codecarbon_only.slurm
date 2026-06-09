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
export PYTHONPATH=/opt/rocm-7.0.1/share/amd_smi:$PYTHONPATH

rocm-smi
rocm-smi --showpower --showtemp --showmeminfo vram --showenergy --json
rocm-smi --version

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the Python script
echo "=== Starting CodeCarbon Test ==="
source .venv-codecarbon/bin/activate
python3 -m pip list | grep -E "(torch|amd)"
# Verify activation (optional)
which python3
python3 --version

echo "=== Running Training Script ==="
srun python no_load.py
