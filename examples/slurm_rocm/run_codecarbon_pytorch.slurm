#!/bin/bash
#SBATCH --account=cad15147
#SBATCH --constraint=MI250
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
# DO NOT 'module load rocm' here as it pollutes LD_LIBRARY_PATH and breaks the PyTorch wheel's LLVM/Comgr!
# We just manually set ROCM_PATH so amdsmi wrapper works.
# export ROCM_PATH=/opt/rocm-7.0.1
module load python/3.12
export PYTHONPATH=/opt/rocm-7.0.1/share/amd_smi:$PYTHONPATH


# For Adastra's MI250 nodes managed by SLURM, overriding HIP_VISIBLE_DEVICES completely breaks PyTorch visibility!
# We MUST NOT override HIP_VISIBLE_DEVICES and must allow the ROCm driver to consume ROCR_VISIBLE_DEVICES natively.
#export HIP_LAUNCH_BLOCKING=1
#export MPICH_GPU_SUPPORT_ENABLED=1
# Important: To bypass the "HIP error: invalid argument" on Adastra, we don't change device IDs.
# We change the way PyTorch maps memory using the underlying allocator.
# export PYTORCH_HIP_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:128

# Extended Debugging Variables for Segmentation Faults
#export TORCH_SHOW_CPP_STACKTRACES=1
#export PYTORCH_NO_CUDA_MEMORY_CACHING=1
#export AMD_LOG_LEVEL=4
#export HSAKMT_DEBUG_LEVEL=7

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

# Test PyTorch ROCm detection
echo "=== PyTorch ROCm Test ==="
# Set environment flags to serialize HIP kernel execution so the segfault throws at the exact call
#export AMD_SERIALIZE_KERNEL=1
#export HSA_ENABLE_SDMA=0

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
# On Adastra, we need srun to bind the GPU even within sbatch
# Try the GPU stress test using ROCm utilities
# pip install flash-attn --no-build-isolation
# python transformer_onnx.py
# python transformer_flash.py
# srun \
#   --kill-on-bad-exit=1 \
#   --gpu-bind=closest \
#   bash -c "catchsegv python pytorch_matrix.py; dmesg -T | tail -n 50"

srun python examples/slurm_rocm/pytorch_matrix.py