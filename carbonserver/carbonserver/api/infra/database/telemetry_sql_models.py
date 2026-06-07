"""SQLAlchemy models for telemetry data in the CarbonServer API."""

import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from carbonserver.database.database import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False)
    telemetry_level = Column(String, nullable=False)

    os = Column(String, nullable=True)
    country_name = Column(String, nullable=True)
    country_iso_code = Column(String, nullable=True)
    region = Column(String, nullable=True)
    cloud_provider = Column(String, nullable=True)
    cloud_region = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    cpu_count = Column(Integer, nullable=True)
    cpu_physical_count = Column(Integer, nullable=True)
    cpu_model = Column(String, nullable=True)
    cpu_architecture = Column(String, nullable=True)
    gpu_count = Column(Integer, nullable=True)
    gpu_model = Column(String, nullable=True)
    gpu_driver_version = Column(String, nullable=True)
    gpu_memory_total_gb = Column(Float, nullable=True)
    ram_total_size_gb = Column(Float, nullable=True)
    cuda_version = Column(String, nullable=True)
    cudnn_version = Column(String, nullable=True)

    python_version = Column(String, nullable=True)
    python_implementation = Column(String, nullable=True)
    python_executable_hash = Column(String, nullable=True)
    python_env_type = Column(String, nullable=True)
    codecarbon_version = Column(String, nullable=True)
    codecarbon_install_method = Column(String, nullable=True)

    total_emissions_kg = Column(Float, nullable=True)
    emissions_rate_kg_per_sec = Column(Float, nullable=True)
    energy_consumed_kwh = Column(Float, nullable=True)
    cpu_energy_kwh = Column(Float, nullable=True)
    gpu_energy_kwh = Column(Float, nullable=True)
    ram_energy_kwh = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    cpu_utilization_avg = Column(Float, nullable=True)
    gpu_utilization_avg = Column(Float, nullable=True)
    ram_utilization_avg = Column(Float, nullable=True)

    tracking_mode = Column(String, nullable=True)
    api_mode = Column(String, nullable=True)
    output_methods = Column(JSON, nullable=True)
    hardware_tracked = Column(JSON, nullable=True)
    task_tracking_used = Column(Boolean, nullable=True)
    decorator_vs_context = Column(String, nullable=True)
    measure_power_interval_secs = Column(Float, nullable=True)

    hardware_detection_success = Column(Boolean, nullable=True)
    rapl_available = Column(Boolean, nullable=True)
    gpu_detection_method = Column(String, nullable=True)
    first_measurement_time_ms = Column(Float, nullable=True)
    tracking_overhead_percent = Column(Float, nullable=True)
    errors_encountered = Column(JSON, nullable=True)
    warning_count = Column(Integer, nullable=True)

    ide_used = Column(String, nullable=True)
    notebook_environment = Column(String, nullable=True)
    ci_environment = Column(String, nullable=True)
    python_package_manager = Column(String, nullable=True)
    framework_detected = Column(String, nullable=True)

    has_torch = Column(Boolean, nullable=True)
    torch_version = Column(String, nullable=True)
    has_transformers = Column(Boolean, nullable=True)
    transformers_version = Column(String, nullable=True)
    has_diffusers = Column(Boolean, nullable=True)
    diffusers_version = Column(String, nullable=True)
    has_tensorflow = Column(Boolean, nullable=True)
    tensorflow_version = Column(String, nullable=True)
    has_keras = Column(Boolean, nullable=True)
    keras_version = Column(String, nullable=True)
    has_pytorch_lightning = Column(Boolean, nullable=True)
    pytorch_lightning_version = Column(String, nullable=True)
    has_fastai = Column(Boolean, nullable=True)
    fastai_version = Column(String, nullable=True)
    ml_framework_primary = Column(String, nullable=True)

    container_runtime = Column(String, nullable=True)
    in_container = Column(Boolean, nullable=True)
    host_machine_hash = Column(String, nullable=True)

    def __repr__(self):
        return (
            f'<Telemetry(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'telemetry_level="{self.telemetry_level}")>'
        )
