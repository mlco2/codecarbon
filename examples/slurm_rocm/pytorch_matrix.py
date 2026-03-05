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
from concurrent.futures import ThreadPoolExecutor

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
    """Select and configure devices (all GPUs or CPU)."""
    if not torch.cuda.is_available():
        logger.warning("ROCm/AMD GPU is not available. Using CPU instead.")
        return [torch.device("cpu")], 4096

    num_gpus = torch.cuda.device_count()
    logger.info(f"PyTorch sees {num_gpus} GPU(s)")

    devices = [torch.device(f"cuda:{i}") for i in range(num_gpus)]
    for i in range(len(devices)):
        logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    sys.stdout.flush()

    _log_gpu_memory_info(devices)
    return devices, 4096


def _log_gpu_memory_info(devices):
    """Log GPU memory information if available."""
    try:
        for i, device in enumerate(devices):
            if device.type == "cuda":
                total_memory = torch.cuda.get_device_properties(i).total_memory / (
                    1024**3
                )
                logger.info(f"GPU {i} - Total memory: {total_memory:.2f} GB")
                logger.info(
                    f"  Allocated: {torch.cuda.memory_allocated(i) / (1024**3):.2f} GB"
                )
                logger.info(
                    f"  Cached: {torch.cuda.memory_reserved(i) / (1024**3):.2f} GB"
                )
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Could not get GPU memory info: {e}")
        sys.stdout.flush()


def _allocate_matrix(devices, matrix_size):
    """Allocate matrix tensors on all devices with fallback to smaller size on failure."""
    logger.info(
        f"Allocating matrices of size {matrix_size}x{matrix_size} on {len(devices)} device(s)..."
    )
    logger.info(
        f"Expected memory: ~{(matrix_size * matrix_size * 4) / (1024**3):.2f} GB per matrix per device"
    )
    logger.info("Creating matrices with fixed values...")
    sys.stdout.flush()

    matrices = []
    try:
        for i, device in enumerate(devices):
            matrix = torch.full(
                (matrix_size, matrix_size), 0.5, device=device, dtype=torch.float32
            )
            if device.type == "cuda":
                torch.cuda.synchronize(device)
                alloc_gb = torch.cuda.memory_allocated(i) / (1024**3)
                logger.info(
                    f"Device {i}: Matrix created. GPU memory: {alloc_gb:.2f} GB"
                )
            matrices.append(matrix)
        logger.info("All matrices created and initialized successfully")
        sys.stdout.flush()
        return matrices
    except Exception as e:
        logger.error(f"Failed to allocate matrices: {e}")
        if any(d.type == "cuda" for d in devices):
            logger.info("Trying with smaller matrix size (2048)...")
            matrices = []
            for device in devices:
                matrix = torch.full(
                    (2048, 2048), 0.5, device=device, dtype=torch.float32
                )
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                matrices.append(matrix)
            logger.info("Matrices created successfully with reduced size 2048")
            sys.stdout.flush()
            return matrices
        raise


def _run_rocm_smi_check():
    """Run rocm-smi command and log output."""
    try:
        result = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=5)
        logger.info("GPU visible to rocm-smi:")
        logger.info(result.stdout)
    except Exception as e:
        logger.warning(f"Could not run rocm-smi: {e}")


def _run_computation_on_device(device, matrix, duration):
    """Run computation on a single device for the specified duration."""
    start_time = time.time()
    iteration = 0
    result = None

    while time.time() - start_time < duration:
        result = torch.mm(matrix, matrix)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        iteration += 1

    return result, iteration, time.time() - start_time


def _run_computation_loop(devices, matrices):
    """Run the main computation loop for 120 seconds on all devices in parallel."""
    logger.info(f"Starting computation loop on {len(devices)} device(s)...")
    sys.stdout.flush()

    start_time = time.time()
    duration = 120
    last_print_time = 0
    results = []
    iterations = []

    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        # Submit computation tasks for all devices
        futures = []
        for device, matrix in zip(devices, matrices):
            future = executor.submit(
                _run_computation_on_device, device, matrix, duration
            )
            futures.append(future)

        # Monitor progress while computations run in parallel
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            if int(elapsed) // 10 > last_print_time // 10:
                logger.info(
                    f"Progress: {elapsed:.1f}s / {duration}s (computing on {len(devices)} device(s))"
                )
                sys.stdout.flush()
                last_print_time = elapsed
                _run_rocm_smi_check()

        # Collect results from all devices
        for i, future in enumerate(futures):
            result, iteration, elapsed = future.result()
            results.append(result)
            iterations.append(iteration)
            logger.info(f"Device {i}: {iteration} iterations in {elapsed:.2f}s")

    total_elapsed = time.time() - start_time
    total_iterations = sum(iterations)
    return results, total_iterations, total_elapsed


def _cleanup_resources(devices, results, matrices):
    """Clean up GPU and tensor resources."""
    logger.info("Cleaning up resources...")
    sys.stdout.flush()
    del results
    del matrices
    for device in devices:
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
        devices, matrix_size = _select_device()

        logger.info(
            f"Starting GPU-intensive computation for 120 seconds with matrix size {matrix_size}..."
        )
        sys.stdout.flush()

        matrices = _allocate_matrix(devices, matrix_size)

        if any(d.type == "cuda" for d in devices):
            for i, device in enumerate(devices):
                if device.type == "cuda":
                    logger.info(
                        f"Final GPU {i} memory: {torch.cuda.memory_allocated(i) / (1024**3):.2f} GB"
                    )
            sys.stdout.flush()

        results, total_iterations, elapsed = _run_computation_loop(devices, matrices)
        _cleanup_resources(devices, results, matrices)

        logger.info(
            f"Completed! Total time: {elapsed:.2f}s, Total iterations: {total_iterations}"
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
            num_gpus = torch.cuda.device_count()
            for gpu_id in range(num_gpus):
                logger.info(f"  Initializing GPU {gpu_id}...")
                sys.stdout.flush()

                logger.info(
                    f"    Step 1: Setting up device targeting logical id {gpu_id}..."
                )
                sys.stdout.flush()
                dev = torch.device(f"cuda:{gpu_id}")

                logger.info("    Step 2: Checking memory parameters before alloc...")
                sys.stdout.flush()
                _ = torch.cuda.get_device_properties(gpu_id)

                logger.info("    Step 3: Triggering C++ allocator backend...")
                sys.stdout.flush()
                # Try to force the memory caching allocator initialization directly using raw zero tensor which is more robust than scalar
                a = torch.zeros((1,), device=dev)
                logger.info("      Allocation complete.")
                sys.stdout.flush()

                logger.info("    Step 4: Synchronizing device...")
                sys.stdout.flush()
                torch.cuda.synchronize(dev)
                logger.info(f"  GPU {gpu_id} initialized successfully.")
                sys.stdout.flush()

            logger.info("All PyTorch ROCm contexts initialized successfully.")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"PyTorch context initialization FAILED: {str(e)}")
            sys.stdout.flush()
            raise

    model = train_model()
    logger.info("Script finished.")
    sys.stdout.flush()
