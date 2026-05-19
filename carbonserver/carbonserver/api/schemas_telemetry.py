"""Schemas for telemetry data submitted to the CarbonServer API."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TelemetryLevel(str, Enum):
    disabled = "disabled"
    minimal = "minimal"
    extensive = "extensive"


class TelemetryBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "timestamp": "2026-05-03T12:00:00+00:00",
                "telemetry_level": "minimal",
                "os": "Linux-5.10.0-x86_64",
                "country_name": "France",
                "country_iso_code": "FRA",
                "cpu_count": 12,
                "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
                "python_version": "3.11.5",
                "codecarbon_version": "3.0.0",
            }
        },
    )

    timestamp: datetime
    telemetry_level: TelemetryLevel

    os: Optional[str] = None
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = Field(default=None, min_length=2, max_length=3)
    region: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    on_cloud: Optional[bool] = None

    cpu_count: Optional[int] = Field(default=None, ge=0)
    cpu_physical_count: Optional[int] = Field(default=None, ge=0)
    cpu_model: Optional[str] = None
    cpu_architecture: Optional[str] = None
    gpu_count: Optional[int] = Field(default=None, ge=0)
    gpu_model: Optional[str] = None
    gpu_driver_version: Optional[str] = None
    gpu_memory_total_gb: Optional[float] = Field(default=None, ge=0)
    ram_total_size_gb: Optional[float] = Field(default=None, ge=0)
    cuda_version: Optional[str] = None
    cudnn_version: Optional[str] = None

    python_version: Optional[str] = None
    python_implementation: Optional[str] = None
    python_env_type: Optional[str] = None
    codecarbon_version: Optional[str] = None
    codecarbon_install_method: Optional[str] = None
    python_package_manager: Optional[str] = None

    total_emissions_kg: Optional[float] = Field(default=None, ge=0)
    emissions_rate_kg_per_sec: Optional[float] = Field(default=None, ge=0)
    energy_consumed_kwh: Optional[float] = Field(default=None, ge=0)
    cpu_energy_kwh: Optional[float] = Field(default=None, ge=0)
    gpu_energy_kwh: Optional[float] = Field(default=None, ge=0)
    ram_energy_kwh: Optional[float] = Field(default=None, ge=0)
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    cpu_utilization_avg: Optional[float] = Field(default=None, ge=0, le=100)
    gpu_utilization_avg: Optional[float] = Field(default=None, ge=0, le=100)
    ram_utilization_avg: Optional[float] = Field(default=None, ge=0, le=100)

    tracking_mode: Optional[str] = None
    api_mode: Optional[str] = None
    output_methods: Optional[List[str]] = None
    hardware_tracked: Optional[List[str]] = None
    task_tracking_used: Optional[bool] = None
    measure_power_interval_secs: Optional[float] = Field(default=None, ge=0)
    integration_surface: Optional[str] = None
    offline_mode: Optional[bool] = None
    save_to_api_enabled: Optional[bool] = None

    hardware_detection_success: Optional[bool] = None
    rapl_available: Optional[bool] = None
    gpu_detection_method: Optional[str] = None

    ide_used: Optional[str] = None
    notebook_environment: Optional[str] = None
    ci_environment: Optional[str] = None
    framework_detected: Optional[str] = None

    has_torch: Optional[bool] = None
    torch_version: Optional[str] = None
    has_transformers: Optional[bool] = None
    transformers_version: Optional[str] = None
    has_diffusers: Optional[bool] = None
    diffusers_version: Optional[str] = None
    has_tensorflow: Optional[bool] = None
    tensorflow_version: Optional[str] = None
    has_keras: Optional[bool] = None
    keras_version: Optional[str] = None
    has_pytorch_lightning: Optional[bool] = None
    pytorch_lightning_version: Optional[str] = None
    has_fastai: Optional[bool] = None
    fastai_version: Optional[str] = None
    ml_framework_primary: Optional[str] = None

    container_runtime: Optional[str] = None
    in_container: Optional[bool] = None

    @model_validator(mode="after")
    def validate_telemetry_level(self):
        if self.telemetry_level == TelemetryLevel.disabled:
            raise ValueError("Disabled telemetry must not be submitted")
        return self


PRIVATE_TELEMETRY_FIELDS = frozenset(TelemetryBase.model_fields)


class TelemetryCreate(TelemetryBase):
    pass


class Telemetry(TelemetryBase):
    id: str
