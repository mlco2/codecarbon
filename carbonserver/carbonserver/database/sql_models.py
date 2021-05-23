import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from carbonserver.database.database import Base


class Emission(Base):
    __tablename__ = "emissions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    duration = Column(Float)
    emissions = Column(Float)
    energy_consumed = Column(Float)
    run_id = Column(String, ForeignKey("runs.id"))
    run = relationship("Run", back_populates="emissions")

    def __repr__(self):
        return (
            f'<Emission(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'emissions="{self.emissions}", '
            f'run_id="{self.run_id}")>'
        )


class Run(Base):
    __tablename__ = "runs"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    experiment = relationship("Experiment", back_populates="runs")
    emissions = relationship("Emission", back_populates="run")

    def __repr__(self):
        return (
            f'<Run(id="{self.id}", '
            f'timestamp="{self.timestamp}", '
            f'experiment_id="{self.run_id}")>'
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
    project_id = Column(Integer, ForeignKey("projects.id"))
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
    team_id = Column(Integer, ForeignKey("teams.id"))
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
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    projects = relationship("Project", back_populates="team")
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
    teams = relationship("Team", back_populates="organization")

    def __repr__(self):
        return (
            f'<Team(id="{self.id}", '
            f'name="{self.name}", '
            f'description="{self.description}")>'
        )


class User(Base):
    __tablename__ = "users"
    user_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String)
    is_active = Column(Boolean, default=True)
    # TODO: Associate user with his entities

    def __repr__(self):
        return (
            f'<User(user_id="{self.user_id}", '
            f'name="{self.name}", '
            f'is_active="{self.is_active}", '
            f'email="{self.email}")>'
        )
