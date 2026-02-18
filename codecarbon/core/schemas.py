"""
Here is the schemas used to communicate with the API.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class EmissionBase:
    timestamp: str
    run_id: str
    duration: int
    emissions_sum: float
    emissions_rate: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float


class EmissionCreate(EmissionBase):
    pass


class Emission(EmissionBase):
    id: str


@dataclass
class RunBase:
    timestamp: str
    experiment_id: str
    os: Optional[str]
    python_version: Optional[str]
    codecarbon_version: Optional[str]
    cpu_count: Optional[int]
    cpu_model: Optional[str]
    gpu_count: Optional[int]
    gpu_model: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    region: Optional[str]
    provider: Optional[str]
    ram_total_size: Optional[float]
    tracking_mode: Optional[str]


class RunCreate(RunBase):
    pass


class Run(RunBase):
    id: str


@dataclass
class ExperimentBase:
    timestamp: datetime
    name: str
    description: str
    on_cloud: bool
    project_id: UUID
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = None
    region: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None


class ExperimentCreate(ExperimentBase):
    pass


class Experiment(ExperimentBase):
    id: str


@dataclass
class OrganizationBase:
    name: str
    description: str


class OrganizationCreate(OrganizationBase):
    pass


class Organization(OrganizationBase):
    id: str


@dataclass
class ProjectBase:
    name: str
    description: str
    organization_id: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
