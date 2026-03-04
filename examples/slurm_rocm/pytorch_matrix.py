"""
pip install --upgrade pip
pip install amdsmi==6.4.3
pip3 install torch==2.9.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.4
pip install numpy
"""

import logging
import os
import subprocess
import sys
import time

import torch

from codecarbon import track_emissions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
# Force flush after each log
for handler in logger.handlers:
    handler.flush = lambda: sys.stdout.flush()


def _log_environment():
    """Log environment variables and GPU availability."""
    logger.info("Checking if ROCm/AMD GPU is available...")
    logger.info(
        f"ROCR_VISIBLE_DEVICES: {os.environ.get('ROCR_VISIBLE_DEVICES', 'not set')}"
    )
    logger.info(
        f"HIP_VISIBLE_DEVICES: {os.environ.get('HIP_VISIBLE_DEVICES', 'not set')}"
    )
    logger.info(
        f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')}"
    )
    sys.stdout.flush()


def _select_device():
    """Select and configure device (GPU or CPU)."""
    if not torch.cuda.is_available():
        logger.warning("ROCm/AMD GPU is not available. Using CPU instead.")
        return torch.device("cpu"), 4096

    logger.info(f"PyTorch sees {torch.cuda.device_count()} GPU(s)")
    logger.info(f"Using AMD GPU: {torch.cuda.get_device_name(0)}")
    sys.stdout.flush()

    _log_gpu_memory_info()
    return torch.device("cuda:0"), 4096


def _log_gpu_memory_info():
    """Log GPU memory information if available."""
    try:
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        logger.info(f"Total GPU memory: {total_memory:.2f} GB")
        logger.info(f"Allocated: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB")
        logger.info(f"Cached: {torch.cuda.memory_reserved(0) / (1024**3):.2f} GB")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Could not get GPU memory info: {e}")
        sys.stdout.flush()


def _allocate_matrix(device, matrix_size):
    """Allocate matrix tensor with fallback to smaller size on failure."""
    logger.info(f"Allocating matrix of size {matrix_size}x{matrix_size}...")
    logger.info(
        f"Expected memory: ~{(matrix_size * matrix_size * 4) / (1024**3):.2f} GB per matrix"
    )
    logger.info("Creating matrix with fixed values on GPU...")
    sys.stdout.flush()

    try:
        matrix = torch.full(
            (matrix_size, matrix_size), 0.5, device=device, dtype=torch.float32
        )
        if device.type == "cuda":
            torch.cuda.synchronize()
            logger.info(
                f"Matrix created. GPU memory: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB"
            )
        logger.info("Matrix created and initialized successfully")
        sys.stdout.flush()
        return matrix
    except Exception as e:
        logger.error(f"Failed to allocate matrix: {e}")
        if device.type == "cuda":
            logger.info("Trying with smaller matrix size (2048)...")
            matrix = torch.full((2048, 2048), 0.5, device=device, dtype=torch.float32)
            torch.cuda.synchronize()
            logger.info("Matrix created successfully with reduced size 2048")
            sys.stdout.flush()
            return matrix
        raise


def _run_rocm_smi_check():
    """Run rocm-smi command and log output."""
    try:
        result = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=5)
        logger.info("GPU visible to rocm-smi:")
        logger.info(result.stdout)
    except Exception as e:
        logger.warning(f"Could not run rocm-smi: {e}")


def _run_computation_loop(device, matrix):
    """Run the main computation loop for 120 seconds."""
    logger.info("Starting computation loop...")
    sys.stdout.flush()

    start_time = time.time()
    duration = 120
    iteration = 0
    last_print_time = 0
    result = None

    while time.time() - start_time < duration:
        result = torch.mm(matrix, matrix)
        if device.type == "cuda":
            torch.cuda.synchronize()

        iteration += 1
        elapsed = time.time() - start_time

        if int(elapsed) // 10 > last_print_time // 10:
            logger.info(
                f"Progress: {elapsed:.1f}s / {duration}s (iteration {iteration})"
            )
            sys.stdout.flush()
            last_print_time = elapsed
            _run_rocm_smi_check()

    return result, iteration, time.time() - start_time


def _cleanup_resources(device, result, matrix):
    """Clean up GPU and tensor resources."""
    logger.info("Cleaning up resources...")
    sys.stdout.flush()
    del result
    del matrix
    if device.type == "cuda":
        torch.cuda.empty_cache()


@track_emissions(
    measure_power_secs=5,
    log_level="debug",
)
def train_model():
    """
    Performs GPU-intensive computation for 2 minutes at 100% load using ROCm AMD GPU.
    """
    logger.info("=" * 60)
    logger.info("STARTING TRAIN_MODEL FUNCTION")
    logger.info("=" * 60)
    sys.stdout.flush()

    try:
        _log_environment()
        device, matrix_size = _select_device()

        logger.info(
            f"Starting GPU-intensive computation for 120 seconds with matrix size {matrix_size}..."
        )
        sys.stdout.flush()

        matrix = _allocate_matrix(device, matrix_size)

        if device.type == "cuda":
            logger.info(
                f"Final GPU memory: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB"
            )
            sys.stdout.flush()

        result, iteration, elapsed = _run_computation_loop(device, matrix)
        _cleanup_resources(device, result, matrix)

        logger.info(
            f"Completed! Total time: {elapsed:.2f}s, Total iterations: {iteration}"
        )
        logger.info("=" * 60)
        sys.stdout.flush()

    except RuntimeError as e:
        logger.error(f"Runtime error occurred: {e}")
        sys.stdout.flush()
        if "out of memory" in str(e).lower():
            logger.error("GPU out of memory. Try reducing matrix_size.")
        sys.stdout.flush()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.stdout.flush()
        raise


if __name__ == "__main__":
    logger.info("Starting training script...")
    sys.stdout.flush()

    # Pre-initialize PyTorch ROCm context BEFORE CodeCarbon starts its background thread
    if torch.cuda.is_available():
        logger.info("Pre-initializing PyTorch ROCm context...")
        sys.stdout.flush()
        try:
            logger.info("  Step 1: Setting up device targeting logical id 0...")
            sys.stdout.flush()
            dev0 = torch.device("cuda:0")

            logger.info("  Step 2: Checking memory parameters before alloc...")
            sys.stdout.flush()
            _ = torch.cuda.get_device_properties(0)

            logger.info("  Step 3: Triggering C++ allocator backend...")
            sys.stdout.flush()
            # Try to force the memory caching allocator initialization directly using raw zero tensor which is more robust than scalar
            a = torch.zeros((1,), device=dev0)
            logger.info("    Allocation complete.")
            sys.stdout.flush()

            logger.info("  Step 4: Synchronizing device...")
            sys.stdout.flush()
            torch.cuda.synchronize(dev0)
            logger.info("PyTorch ROCm context initialized successfully.")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"PyTorch context initialization FAILED: {str(e)}")
            sys.stdout.flush()
            raise

    model = train_model()
    logger.info("Script finished.")
    sys.stdout.flush()
