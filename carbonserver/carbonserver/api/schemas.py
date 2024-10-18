"""
https://fastapi.tiangolo.com/tutorial/sql-databases/

To avoid confusion between the SQLAlchemy models and the Pydantic models, we will have the file models.py with the SQLAlchemy models, and the file schemas.py with the Pydantic models.

These Pydantic models define more or less a "schema" (a valid data shape).

So this will help us avoiding confusion while using both.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Extra, Field, SecretStr

class Empty(BaseModel, extra=Extra.forbid):
    pass


class UserBase(BaseModel):
    email: str


class UserAutoCreate(UserBase):
    name: str
    email: EmailStr
    id: UUID


class UserAuthenticate(UserBase):
    password: SecretStr


class User(UserBase):
    id: UUID
    name: str
    email: EmailStr
    organizations: Optional[List[UUID | str]]  # TODO: cleanup type
    is_active: bool

    class Config:
        orm_mode = True


class EmissionBase(BaseModel):
    timestamp: datetime
    run_id: UUID
    duration: int = Field(
        ..., gt=0, description="The duration must be greater than zero"
    )
    emissions_sum: Optional[float] = Field(
        ..., ge=0, description="The emissions must be greater than zero"
    )
    emissions_rate: Optional[float] = Field(
        ..., ge=0, description="The emissions rate must be greater than zero"
    )
    energy_consumed: Optional[float] = Field(
        ..., ge=0, description="The energy_consumed must be greater than zero"
    )
    cpu_power: Optional[float] = Field(
        ..., ge=0, description="The cpu_power must be greater than zero"
    )
    gpu_power: Optional[float] = Field(
        ..., ge=0, description="The gpu_power must be greater than zero"
    )
    ram_power: Optional[float] = Field(
        ..., ge=0, description="The ram_power must be greater than zero"
    )
    cpu_energy: Optional[float] = Field(
        ..., ge=0, description="The cpu_energy must be greater than zero"
    )
    gpu_energy: Optional[float] = Field(
        ..., ge=0, description="The gpu_energy must be greater than zero"
    )
    ram_energy: Optional[float] = Field(
        ..., ge=0, description="The ram_energy must be greater than zero"
    )

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

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2021-04-04T08:43:00+02:00",
                "experiment_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
                "os": "macOS-10.15.7-x86_64-i386-64bit",
                "python_version": "3.8.0",
                "codecarbon_version": "2.1.3",
                "cpu_count": 12,
                "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
                "gpu_count": 4,
                "gpu_model": "NVIDIA",
                "longitude": -7.6174,
                "latitude": 33.5822,
                "region": "EUROPE",
                "provider": "AWS",
                "ram_total_size": 83948.22,
                "tracking_mode": "Machine",
            }
        }


class RunCreate(RunBase):
    pass


class Run(RunBase):
    id: UUID


class RunReport(RunBase):
    run_id: UUID
    timestamp: datetime
    experiment_id: Optional[UUID]
    emissions: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float
    duration: float
    emissions_rate: float
    emissions_count: int


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


class ExperimentReport(ExperimentBase):
    experiment_id: UUID
    timestamp: datetime
    name: str
    description: str
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = None
    region: Optional[str] = None
    on_cloud: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    emissions: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float
    duration: int
    emissions_rate: float
    emissions_count: int

    class Config:
        schema_extra = {
            "experiment_id": "943b2aa5-9e21-41a9-8a38-562505b4b2aa",
            "timestamp": "2021-10-07T20:19:27.716693",
            "name": "Code Carbon user test",
            "description": "Code Carbon user test with default project",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "france",
            "on_cloud": False,
            "cloud_provider": None,
            "cloud_region": None,
            "emission": 152.28955200363455,
            "cpu_power": 5760,
            "gpu_power": 2983.9739999999993,
            "ram_power": 806.0337192959997,
            "cpu_energy": 191.8251863024175,
            "gpu_energy": 140.01098718681496,
            "ram_energy": 26.84332784201141,
            "energy_consumed": 358.6795013312438,
            "duration": 7673204,
            "emissions_rate": 1.0984556074701752,
            "emissions_count": 64,
        }


class ProjectBase(BaseModel):
    name: str
    description: str
    organization_id: UUID

    class Config:
        schema_extra = {
            "example": {
                "name": "API Code Carbon",
                "description": "API for Code Carbon",
                "organization_id": "Code Carbon organization",
            }
        }


class ProjectCreate(ProjectBase):
    pass


class ProjectPatch(BaseModel):
    name: Optional[str]
    description: Optional[str]

    # do not allow the organization_id

    class Config:
        schema_extra = {
            "example": {
                "name": "API Code Carbon",
                "description": "API for Code Carbon",
            }
        }


class AccessLevel(Enum):
    READ = 1
    WRITE = 2
    READ_WRITE = 3


# Used in the responses to the user
class ProjectToken(BaseModel):
    id: UUID
    project_id: UUID
    name: Optional[str]
    token: Optional[str] = None
    last_used: Optional[datetime] = None
    access: int = AccessLevel.WRITE.value
    revoked: bool = False

    class Config:
        schema_extra = {
            "example": {
                "id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
                "project_id": "8edb03e1-9a28-452a-9c93-a3b6560136d7",
                "name": "my project token",
                "last_used": "2021-04-04T08:43:00+02:00",
                "access": 1,
                "revoked": False,
            }
        }

# Used to handle responses from the database
class ProjectTokenInternal(ProjectToken):
    id: Optional[str]
    hashed_token: str

class ProjectTokenCreate(BaseModel):
    name: Optional[str]
    access: int = AccessLevel.WRITE.value

    class Config:
        schema_extra = {
            "example": {
                "name": "my project token",
                "access": 1,
            }
        }


class Project(ProjectBase):
    id: UUID
    experiments: Optional[List[str]] = []


class ProjectReport(ProjectBase):
    project_id: UUID
    name: str
    description: str
    emissions: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float
    duration: int
    emissions_rate: float
    emissions_count: int


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


class OrganizationPatch(OrganizationBase):
    name: Optional[str]
    description: Optional[str]


class Organization(OrganizationBase):
    id: UUID


class OrganizationReport(OrganizationBase):
    organization_id: UUID
    name: str
    description: str
    emissions: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float
    duration: int
    emissions_rate: float
    emissions_count: int


class Membership(BaseModel):
    user_id = UUID
    organization_id = UUID
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class OrganizationUser(User):
    organization_id = UUID
    is_admin: bool
