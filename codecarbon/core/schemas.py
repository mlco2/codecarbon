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
