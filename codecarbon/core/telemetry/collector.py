"""
Telemetry data collector.

Collects environment, hardware, usage, and ML ecosystem data.
"""

import hashlib
import os
import platform
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from codecarbon._version import __version__
from codecarbon.core.config import get_hierarchical_config
from codecarbon.external.logger import logger


@dataclass
class TelemetryData:
    """Container for all telemetry data."""

    # Environment & Hardware (Tier 1: Internal)
    os: str = ""
    python_version: str = ""
    python_implementation: str = ""
    python_executable_hash: str = ""
    python_env_type: str = ""
    codecarbon_version: str = ""
    codecarbon_install_method: str = ""

    cpu_count: int = 0
    cpu_physical_count: int = 0
    cpu_model: str = ""
    cpu_architecture: str = ""

    gpu_count: int = 0
    gpu_model: str = ""
    gpu_driver_version: str = ""
    gpu_memory_total_gb: float = 0.0

    ram_total_size_gb: float = 0.0

    cuda_version: str = ""
    cudnn_version: str = ""

    cloud_provider: str = ""
    cloud_region: str = ""

    # Usage Patterns (Tier 1: Internal)
    tracking_mode: str = ""
    api_mode: str = ""  # offline, online
    output_methods: list = field(default_factory=list)
    hardware_tracked: list = field(default_factory=list)
    measure_power_interval_secs: float = 15.0

    # ML Ecosystem (Tier 1: Internal)
    has_torch: bool = False
    torch_version: str = ""
    has_transformers: bool = False
    transformers_version: str = ""
    has_diffusers: bool = False
    diffusers_version: str = ""
    has_tensorflow: bool = False
    tensorflow_version: str = ""
    has_keras: bool = False
    keras_version: str = ""
    has_pytorch_lightning: bool = False
    pytorch_lightning_version: str = ""
    has_fastai: bool = False
    fastai_version: str = ""
    ml_framework_primary: str = ""

    # Performance & Errors (Tier 1: Internal)
    hardware_detection_success: bool = True
    rapl_available: bool = False
    gpu_detection_method: str = ""
    errors_encountered: list = field(default_factory=list)
    tracking_overhead_percent: float = 0.0

    # Context (Tier 1: Internal)
    ide_used: str = ""
    notebook_environment: str = ""
    ci_environment: str = ""
    python_package_manager: str = ""
    container_runtime: str = ""
    in_container: bool = False

    # Emissions Data (Tier 2: Public only)
    total_emissions_kg: float = 0.0
    emissions_rate_kg_per_sec: float = 0.0
    energy_consumed_kwh: float = 0.0
    cpu_energy_kwh: float = 0.0
    gpu_energy_kwh: float = 0.0
    ram_energy_kwh: float = 0.0
    duration_seconds: float = 0.0
    cpu_utilization_avg: float = 0.0
    gpu_utilization_avg: float = 0.0
    ram_utilization_avg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class TelemetryCollector:
    """Collects telemetry data."""

    def __init__(self):
        self._data = TelemetryData()

    @property
    def data(self) -> TelemetryData:
        return self._data

    def collect_environment(self) -> "TelemetryCollector":
        """Collect Python environment info."""
        self._data.python_version = platform.python_version()
        self._data.python_implementation = platform.python_implementation()

        # Hash executable path for privacy
        executable = sys.executable
        if executable:
            self._data.python_executable_hash = hashlib.sha256(
                executable.encode()
            ).hexdigest()[:16]

        # Detect environment type
        self._data.python_env_type = self._detect_python_env_type()

        # CodeCarbon version
        self._data.codecarbon_version = __version__

        # Install method detection
        self._data.codecarbon_install_method = self._detect_install_method()

        # OS
        self._data.os = platform.platform()

        # Architecture
        self._data.cpu_architecture = platform.machine()

        return self

    def _detect_python_env_type(self) -> str:
        """Detect Python environment type."""
        if "conda" in sys.prefix.lower():
            return "conda"
        elif hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            # Check for common venv patterns
            if os.environ.get("VIRTUAL_ENV"):
                return "venv"
            # Check for uv
            if os.environ.get("UV"):
                return "uv"
            return "virtualenv"
        elif os.environ.get("VIRTUAL_ENV"):
            return "venv"
        elif os.environ.get("UV"):
            return "uv"
        return "system"

    def _detect_install_method(self) -> str:
        """Detect how CodeCarbon was installed."""
        # Check if editable install
        import codecarbon

        codecarbon_path = os.path.dirname(codecarbon.__file__)
        if ".egg-link" in codecarbon_path or ".editable" in codecarbon_path:
            return "editable"

        # Check common package managers
        # This is a heuristic - check if in common locations
        if "site-packages" in codecarbon_path:
            # Could be pip, uv, or conda
            if "uv" in codecarbon_path:
                return "uv"
            elif "conda" in codecarbon_path:
                return "conda"
            return "pip"
        return "unknown"

    def collect_hardware(
        self,
        cpu_count: int = 0,
        cpu_physical_count: int = 0,
        cpu_model: str = "",
        gpu_count: int = 0,
        gpu_model: str = "",
        ram_total_gb: float = 0.0,
    ) -> "TelemetryCollector":
        """Collect hardware info."""
        self._data.cpu_count = cpu_count
        self._data.cpu_physical_count = cpu_physical_count
        self._data.cpu_model = cpu_model
        self._data.ram_total_size_gb = ram_total_gb
        self._data.gpu_count = gpu_count
        self._data.gpu_model = gpu_model

        # Try to detect CUDA
        self._detect_cuda()

        # Try to detect GPU driver
        self._detect_gpu_driver()

        return self

    def _detect_cuda(self) -> None:
        """Detect CUDA version."""
        try:
            import torch

            if hasattr(torch, "version") and torch.version:
                self._data.cuda_version = str(torch.version.cuda)
                if hasattr(torch.backends, "cudnn") and torch.backends.cudnn.is_available():
                    self._data.cudnn_version = str(torch.backends.cudnn.version())
        except ImportError:
            pass

    def _detect_gpu_driver(self) -> None:
        """Detect GPU driver version."""
        try:
            import subprocess

            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._data.gpu_driver_version = result.stdout.strip().split("\n")[0]
                self._data.gpu_detection_method = "nvidia-smi"

                # Also get GPU memory
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    mem_mb = result.stdout.strip().split("\n")[0]
                    self._data.gpu_memory_total_gb = float(mem_mb) / 1024
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

    def collect_usage(
        self,
        tracking_mode: str = "machine",
        api_mode: str = "online",
        output_methods: list = None,
        hardware_tracked: list = None,
        measure_power_interval: float = 15.0,
    ) -> "TelemetryCollector":
        """Collect usage patterns."""
        self._data.tracking_mode = tracking_mode
        self._data.api_mode = api_mode
        self._data.output_methods = output_methods or []
        self._data.hardware_tracked = hardware_tracked or []
        self._data.measure_power_interval_secs = measure_power_interval

        return self

    def collect_ml_ecosystem(self) -> "TelemetryCollector":
        """Detect ML frameworks and libraries."""
        frameworks = []

        # PyTorch
        try:
            import torch

            self._data.has_torch = True
            self._data.torch_version = torch.__version__
            frameworks.append("pytorch")
        except ImportError:
            pass

        # Transformers
        try:
            import transformers

            self._data.has_transformers = True
            self._data.transformers_version = transformers.__version__
        except ImportError:
            pass

        # Diffusers
        try:
            import diffusers

            self._data.has_diffusers = True
            self._data.diffusers_version = diffusers.__version__
        except ImportError:
            pass

        # TensorFlow
        try:
            import tensorflow

            self._data.has_tensorflow = True
            self._data.tensorflow_version = tensorflow.__version__
            frameworks.append("tensorflow")
        except ImportError:
            pass

        # Keras
        try:
            import keras

            self._data.has_keras = True
            self._data.keras_version = keras.__version__
        except ImportError:
            pass

        # PyTorch Lightning
        try:
            import pytorch_lightning

            self._data.has_pytorch_lightning = True
            self._data.pytorch_lightning_version = pytorch_lightning.__version__
        except ImportError:
            pass

        # FastAI
        try:
            import fastai

            self._data.has_fastai = True
            self._data.fastai_version = fastai.__version__
        except ImportError:
            pass

        # Primary framework
        self._data.ml_framework_primary = frameworks[0] if frameworks else ""

        return self

    def collect_context(self) -> "TelemetryCollector":
        """Collect development context (IDE, notebook, CI)."""
        # Detect notebook
        self._data.notebook_environment = self._detect_notebook()

        # Detect CI
        self._data.ci_environment = self._detect_ci()

        # Detect container
        self._detect_container()

        # Detect package manager
        self._data.python_package_manager = self._detect_package_manager()

        return self

    def _detect_notebook(self) -> str:
        """Detect notebook environment."""
        try:
            # Check for Jupyter
            import ipykernel

            return "jupyter"
        except ImportError:
            pass

        # Check environment variables common in cloud notebooks
        if os.environ.get("COLAB_RELEASE_TAG"):
            return "colab"
        if os.environ.get("KAGGLE_URL_BASE"):
            return "kaggle"

        return "none"

    def _detect_ci(self) -> str:
        """Detect CI environment."""
        ci_vars = {
            "GITHUB_ACTIONS": "github-actions",
            "GITLAB_CI": "gitlab",
            "JENKINS_URL": "jenkins",
            "CIRCLECI": "circleci",
            "TRAVIS": "travis",
            "BUILDKITE": "buildkite",
            "AWS_CODEBUILD": "codebuild",
        }

        for var, name in ci_vars.items():
            if os.environ.get(var):
                return name

        return "none"

    def _detect_container(self) -> None:
        """Detect container runtime."""
        # Check for Docker
        if os.path.exists("/.dockerenv"):
            self._data.in_container = True
            self._data.container_runtime = "docker"
            return

        # Check for container environment variables
        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            self._data.in_container = True
            self._data.container_runtime = "kubernetes"
            return

        # Check cgroup
        try:
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "containerd" in content:
                    self._data.in_container = True
                    self._data.container_runtime = "docker"
                    return
        except FileNotFoundError:
            pass

        self._data.in_container = False
        self._data.container_runtime = "none"

    def _detect_package_manager(self) -> str:
        """Detect Python package manager."""
        # Check for poetry
        if os.path.exists("pyproject.toml"):
            with open("pyproject.toml", "r") as f:
                if "[tool.poetry]" in f.read():
                    return "poetry"

        # Check for uv
        if os.path.exists("uv.lock"):
            return "uv"

        # Check for pipenv
        if os.path.exists("Pipfile"):
            return "pipenv"

        # Check for conda
        if os.path.exists("environment.yml") or os.path.exists("environment.yaml"):
            return "conda"

        return "pip"

    def collect_errors(
        self,
        rapl_available: bool = False,
        hardware_detection_success: bool = True,
        errors: list = None,
    ) -> "TelemetryCollector":
        """Collect error information."""
        self._data.rapl_available = rapl_available
        self._data.hardware_detection_success = hardware_detection_success
        self._data.errors_encountered = errors or []

        return self

    def collect_emissions(
        self,
        total_emissions_kg: float = 0.0,
        emissions_rate_kg_per_sec: float = 0.0,
        energy_consumed_kwh: float = 0.0,
        cpu_energy_kwh: float = 0.0,
        gpu_energy_kwh: float = 0.0,
        ram_energy_kwh: float = 0.0,
        duration_seconds: float = 0.0,
        cpu_utilization_avg: float = 0.0,
        gpu_utilization_avg: float = 0.0,
        ram_utilization_avg: float = 0.0,
    ) -> "TelemetryCollector":
        """Collect emissions data (Tier 2: Public)."""
        self._data.total_emissions_kg = total_emissions_kg
        self._data.emissions_rate_kg_per_sec = emissions_rate_kg_per_sec
        self._data.energy_consumed_kwh = energy_consumed_kwh
        self._data.cpu_energy_kwh = cpu_energy_kwh
        self._data.gpu_energy_kwh = gpu_energy_kwh
        self._data.ram_energy_kwh = ram_energy_kwh
        self._data.duration_seconds = duration_seconds
        self._data.cpu_utilization_avg = cpu_utilization_avg
        self._data.gpu_utilization_avg = gpu_utilization_avg
        self._data.ram_utilization_avg = ram_utilization_avg

        return self

    def collect_cloud_info(
        self, cloud_provider: str = "", cloud_region: str = ""
    ) -> "TelemetryCollector":
        """Collect cloud information."""
        self._data.cloud_provider = cloud_provider
        self._data.cloud_region = cloud_region

        return self

    def collect_all(
        self,
        cpu_count: int = 0,
        cpu_physical_count: int = 0,
        cpu_model: str = "",
        gpu_count: int = 0,
        gpu_model: str = "",
        ram_total_gb: float = 0.0,
        tracking_mode: str = "machine",
        api_mode: str = "online",
        output_methods: list = None,
        hardware_tracked: list = None,
        measure_power_interval: float = 15.0,
        rapl_available: bool = False,
        hardware_detection_success: bool = True,
        errors: list = None,
        cloud_provider: str = "",
        cloud_region: str = "",
    ) -> TelemetryData:
        """Collect all available telemetry data."""
        (
            self.collect_environment()
            .collect_hardware(
                cpu_count=cpu_count,
                cpu_physical_count=cpu_physical_count,
                cpu_model=cpu_model,
                gpu_count=gpu_count,
                gpu_model=gpu_model,
                ram_total_gb=ram_total_gb,
            )
            .collect_usage(
                tracking_mode=tracking_mode,
                api_mode=api_mode,
                output_methods=output_methods,
                hardware_tracked=hardware_tracked,
                measure_power_interval=measure_power_interval,
            )
            .collect_ml_ecosystem()
            .collect_context()
            .collect_errors(
                rapl_available=rapl_available,
                hardware_detection_success=hardware_detection_success,
                errors=errors,
            )
            .collect_cloud_info(
                cloud_provider=cloud_provider, cloud_region=cloud_region
            )
        )

        return self._data
