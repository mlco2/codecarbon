#!/bin/bash
#SBATCH --account=cad15147
#SBATCH --constraint=MI300
#SBATCH --nodes=1
#SBATCH --time=0:25:00
#SBATCH --gpus-per-node=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --threads-per-core=1
#SBATCH --job-name=codecarbon-test
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

# Load AMD ROCM environment
module purge
module load cpe/24.07
module load rocm/7.0.1
module load python/3.12
export PYTHONPATH=/opt/rocm-7.0.1/share/amd_smi:$PYTHONPATH

# Print environment info
echo "=== Job Environment ==="
echo "Running on host: $(hostname)"
echo "at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Number of GPUs: $SLURM_GPUS_PER_NODE"
echo "ROCR_VISIBLE_DEVICES: $ROCR_VISIBLE_DEVICES"
echo "HSA_OVERRIDE_GFX_VERSION: $HSA_OVERRIDE_GFX_VERSION"
rocm-smi
rocm-smi --version

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the Python script
echo "=== Starting CodeCarbon Test ==="
source .venv/bin/activate
python3 -m pip list | grep -E "(torch|amd)"
# Verify activation (optional)
which python3
python3 --version

echo "=== PyTorch ROCm Test ==="
python3 << 'EOF'
import os
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"PyTorch built with CUDA: {torch.version.cuda}")
print(f"PyTorch built with HIP: {torch.version.hip if hasattr(torch.version, 'hip') else 'N/A'}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"  ROCR_VISIBLE_DEVICES: {os.environ.get('ROCR_VISIBLE_DEVICES', 'not set')}")

if torch.cuda.is_available():
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
else:
    print("GPU NOT DETECTED - Checking environment:")
    print(f"  HIP_VISIBLE_DEVICES: {os.environ.get('HIP_VISIBLE_DEVICES', 'not set')}")
    print(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')}")
    print(f"  ROCR_VISIBLE_DEVICES: {os.environ.get('ROCR_VISIBLE_DEVICES', 'not set')}")
EOF

echo "=== Running Training Script ==="
srun python examples/slurm_rocm/pytorch_matrix.py
