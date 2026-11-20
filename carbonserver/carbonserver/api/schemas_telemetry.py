"""Schemas for telemetry data submitted to the CarbonServer API."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

#: Every free-text field is capped so one request cannot store unbounded data.
Str = Annotated[str, Field(max_length=256)]


class TelemetryLevel(str, Enum):
    disabled = "disabled"
    minimal = "minimal"


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

    @field_validator("timestamp")
    @classmethod
    def clamp_timestamp(cls, value: datetime) -> datetime:
        """Store at most the current hour (UTC), whatever the client clock says.

        The retention trigger deletes rows by ``timestamp``, so a future value
        would keep a row past the 3 years documented to users.
        """
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = min(value, datetime.now(timezone.utc))
        return value.replace(minute=0, second=0, microsecond=0)

    @model_validator(mode="after")
    def reject_disabled_level(self):
        if self.telemetry_level == TelemetryLevel.disabled:
            raise ValueError("Disabled telemetry must not be submitted")
        return self


class TelemetryCreate(TelemetryBase):
    pass


class Telemetry(TelemetryBase):
    id: str
