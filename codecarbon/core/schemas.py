"""
Here is the schemas used to communicate with the API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union
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


@dataclass
class EmissionCreate(EmissionBase):
    pass


@dataclass
class Emission(EmissionBase):
    id: str = field(default="")


@dataclass
class RunBase:
    timestamp: str
    experiment_id: str
    os: Optional[str] = None
    python_version: Optional[str] = None
    codecarbon_version: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_model: Optional[str] = None
    gpu_count: Optional[int] = None
    gpu_model: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    region: Optional[str] = None
    provider: Optional[str] = None
    ram_total_size: Optional[float] = None
    tracking_mode: Optional[str] = None


@dataclass
class RunCreate(RunBase):
    pass


@dataclass
class Run(RunBase):
    id: str = field(default="")


@dataclass
class ExperimentBase:
    name: str
    description: str
    project_id: Union[UUID, str]
    on_cloud: bool = False
    timestamp: Optional[datetime] = None
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = None
    region: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None


@dataclass
class ExperimentCreate(ExperimentBase):
    pass


@dataclass
class Experiment(ExperimentBase):
    id: str = field(default="")


@dataclass
class OrganizationBase:
    name: str
    description: Optional[str] = ""
    id: Optional[str] = None


@dataclass
class OrganizationCreate(OrganizationBase):
    pass


@dataclass
class Organization(OrganizationBase):
    id: str = field(default="")


@dataclass
class ProjectBase:
    name: str
    organization_id: str
    description: str = ""


@dataclass
class ProjectCreate(ProjectBase):
    pass


@dataclass
class Project(ProjectBase):
    id: str = field(default="")
