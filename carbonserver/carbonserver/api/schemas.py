"""
https://fastapi.tiangolo.com/tutorial/sql-databases/

To avoid confusion between the SQLAlchemy models and the Pydantic models, we will have the file models.py with the SQLAlchemy models, and the file schemas.py with the Pydantic models.

These Pydantic models define more or less a "schema" (a valid data shape).

So this will help us avoiding confusion while using both.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr


class EmissionBase(BaseModel):
    timestamp: datetime
    run_id: UUID
    duration: int = Field(
        ..., gt=0, description="The duration must be greater than zero"
    )
    emissions_sum: float = Field(
        ..., ge=0, description="The emissions must be greater than zero"
    )
    emissions_rate: float = Field(
        ..., ge=0, description="The emissions rate must be greater than zero"
    )
    energy_consumed: float = Field(
        ..., gt=0, description="The energy_consumed must be greater than zero"
    )
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2021-04-04T08:43:00+02:00",
                "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
                "duration": 98745,
                "emissions_sum": 1544.54,
                "emissions_rate": 1.548444,
                "cpu_power": 0.3,
                "gpu_power": 0.0,
                "ram_power": 0.15,
                "cpu_energy": 55.21874,
                "gpu_energy": 0.0,
                "ram_energy": 2.0,
                "energy_consumed": 57.21874,
            }
        }


class EmissionCreate(EmissionBase):
    pass


class Emission(EmissionBase):
    id: UUID


class RunBase(BaseModel):
    timestamp: datetime
    experiment_id: UUID

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2021-04-04T08:43:00+02:00",
                "experiment_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
            }
        }


class RunCreate(RunBase):
    pass


class Run(RunBase):
    id: UUID


class ExperimentBase(BaseModel):
    timestamp: datetime
    name: str
    description: str
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = None
    region: Optional[str] = None
    on_cloud: bool
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    project_id: UUID

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "Run on AWS",
                "description": "AWS API for Code Carbon",
                "timestamp": "2021-04-04T08:43:00+02:00",
                "country_name": "France",
                "country_iso_code": "FRA",
                "region": "france",
                "on_cloud": True,
                "cloud_provider": "aws",
                "cloud_region": "eu-west-1a",
                "project_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
            }
        }


class ExperimentCreate(ExperimentBase):
    pass


class Experiment(ExperimentBase):
    id: UUID


class ProjectBase(BaseModel):
    name: str
    description: str
    team_id: UUID

    class Config:
        schema_extra = {
            "example": {
                "name": "API Code Carbon",
                "description": "API for Code Carbon",
                "team_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
            }
        }


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: UUID
    experiments: Optional[List[Experiment]] = []


class TeamBase(BaseModel):
    name: str
    description: str
    organization_id: UUID

    class Config:
        schema_extra = {
            "example": {
                "name": "Data For Good",
                "description": "Data For Good France",
                "organization_id": "e52fe339-164d-4c2b-a8c0-f562dfce066d",
                "api_key": "default",
            }
        }


class TeamCreate(TeamBase):
    pass


class Team(TeamBase):
    id: UUID
    api_key: str
    organization_id: UUID
    projects: Optional[List[Project]]


class OrganizationBase(BaseModel):
    name: str
    description: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Code Carbon",
                "description": "Save the world, one run at a time.",
            }
        }


class OrganizationCreate(OrganizationBase):
    pass


class Organization(OrganizationBase):
    id: UUID
    api_key: str
    teams: Optional[List[Team]]


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    name: str
    email: EmailStr
    password: SecretStr


class UserAuthenticate(UserBase):
    password: SecretStr


class User(UserBase):
    id: UUID
    name: str
    email: EmailStr
    api_key: str
    organizations: Optional[List]
    teams: Optional[List]
    is_active: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
