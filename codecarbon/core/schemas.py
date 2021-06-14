"""
Here is the schemas used to communicate with the API.
"""
from dataclasses import dataclass


@dataclass
class EmissionBase:
    timestamp: str
    run_id: str
    duration: int
    emissions: float
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
