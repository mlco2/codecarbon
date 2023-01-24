import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import ARRAY

from carbonserver.database.database import Base


class Emission(Base):
    __tablename__ = "emissions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    duration = Column(Float)
    emissions_sum = Column(Float)
    emissions_rate = Column(Float)
    cpu_power = Column(Float)
    gpu_power = Column(Float)
    ram_power = Column(Float)
    cpu_energy = Column(Float)
    gpu_energy = Column(Float)
    ram_energy = Column(Float)
    energy_consumed = Column(Float)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
    run = relationship("Run", back_populates="emissions")

    def __repr__(self):
        return (
            f'<Emission(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'emissions_rate="{self.emissions_rate}", '
            f'run_id="{self.run_id}")>'
        )


class Run(Base):
    __tablename__ = "runs"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"))
    os = Column(String, nullable=True)
    python_version = Column(String, nullable=True)
    codecarbon_version = Column(String, nullable=True)
    cpu_count = Column(Integer, nullable=True)
    cpu_model = Column(String, nullable=True)
    gpu_count = Column(Integer, nullable=True)
    gpu_model = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    region = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    ram_total_size = Column(Float, nullable=True)
    tracking_mode = Column(String, nullable=True)
    experiment = relationship("Experiment", back_populates="runs")
    emissions = relationship("Emission", back_populates="run")

    def __repr__(self):
        return (
            f'<Run(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'experiment_id="{self.experiment_id}")>,'
            f'os="{self.os}")>,'
            f'python_version="{self.python_version}")>,'
            f'codecarbon_version="{self.codecarbon_version}")>,'
            f'cpu_count="{self.cpu_count}")>,'
            f'cpu_model="{self.cpu_model}")>,'
            f'gpu_count="{self.gpu_count}")>,'
            f'gpu_model="{self.gpu_model}")>,'
            f'longitude="{self.longitude}")>,'
            f'latitude="{self.latitude}")>,'
            f'region="{self.region}")>,'
            f'provider="{self.provider}")>,'
            f'ram_total_size="{self.ram_total_size}")>,'
            f'tracking_mode="{self.tracking_mode}")>,'
        )


class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    name = Column(String)
    description = Column(String)
    country_name = Column(String)
    country_iso_code = Column(String)
    region = Column(String)
    on_cloud = Column(Boolean, default=False)
    cloud_provider = Column(String)
    cloud_region = Column(String)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    project = relationship("Project", back_populates="experiments")
    runs = relationship("Run", back_populates="experiment")

    def __repr__(self):
        return (
            f'<Experiment(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'name="{self.name}", '
            f'description="{self.description}", '
            f'region="{self.region}", '
            f'cloud_provider="{self.cloud_provider}", '
            f'cloud_region="{self.cloud_region}", '
            f'project_id="{self.project_id}")>'
        )


class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    experiments = relationship("Experiment", back_populates="project")
    team = relationship("Team", back_populates="projects")

    def __repr__(self):
        return (
            f'<Project(id="{self.id}", '
            f'name="{self.name}", '
            f'description="{self.description}", '
            f'team_id="{self.team_id}")>'
        )


class Team(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    projects = relationship("Project", back_populates="team")
    api_key = Column(String)
    organization = relationship("Organization", back_populates="teams")

    def __repr__(self):
        return (
            f'<Team(id="{self.id}", '
            f'name="{self.name}", '
            f'description="{self.description}", '
            f'organization_id="{self.organization_id}")>'
        )


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    api_key = Column(String)
    teams = relationship("Team", back_populates="organization")

    def __repr__(self):
        return (
            f'<Organization(id="{self.id}", '
            f'name="{self.name}", '
            f'description="{self.description}")>'
        )


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String)
    is_active = Column(Boolean, default=True)
    teams = Column(ARRAY(String, as_tuple=False, dimensions=1))
    organizations = Column(ARRAY(String, as_tuple=False, dimensions=1))

    def __repr__(self):
        return (
            f'<User(id="{self.id}", '
            f'name="{self.name}", '
            f'is_active="{self.is_active}", '
            f'email="{self.email}")>'
        )
