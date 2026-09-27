"""SQLAlchemy models for telemetry data in the CarbonServer API."""

import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String
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
    python_env_type = Column(String, nullable=True)
    codecarbon_version = Column(String, nullable=True)
    codecarbon_install_method = Column(String, nullable=True)

    def __repr__(self):
        return (
            f'<Telemetry(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'telemetry_level="{self.telemetry_level}")>'
        )
