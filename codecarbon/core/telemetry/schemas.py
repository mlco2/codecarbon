"""Telemetry payload schemas aligned with carbonserver ``telemetry_sql_models.Telemetry``."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Every free-text field is capped so one request cannot store unbounded data.
Str = Annotated[str, Field(max_length=256)]


class TelemetryLevel(str, Enum):
    disabled = "disabled"
    minimal = "minimal"


class TelemetryBase(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    timestamp: datetime
    telemetry_level: TelemetryLevel

    os: Optional[Str] = None
    country_name: Optional[Str] = None
    country_iso_code: Optional[str] = Field(default=None, min_length=2, max_length=3)
    region: Optional[Str] = None
    cloud_provider: Optional[Str] = None
    cloud_region: Optional[Str] = None

    cpu_count: Optional[int] = Field(default=None, ge=0)
    cpu_physical_count: Optional[int] = Field(default=None, ge=0)
    cpu_model: Optional[Str] = None
    cpu_architecture: Optional[Str] = None
    gpu_count: Optional[int] = Field(default=None, ge=0)
    gpu_model: Optional[Str] = None
    gpu_driver_version: Optional[Str] = None
    gpu_memory_total_gb: Optional[float] = Field(default=None, ge=0)
    ram_total_size_gb: Optional[float] = Field(default=None, ge=0)
    cuda_version: Optional[Str] = None
    cudnn_version: Optional[Str] = None

    python_version: Optional[Str] = None
    python_implementation: Optional[Str] = None
    python_env_type: Optional[Str] = None
    codecarbon_version: Optional[Str] = None
    codecarbon_install_method: Optional[Str] = None

    @model_validator(mode="after")
    def reject_disabled_level(self):
        if self.telemetry_level == TelemetryLevel.disabled:
            raise ValueError("Disabled telemetry must not be submitted")
        return self


class TelemetryCreate(TelemetryBase):
    pass
