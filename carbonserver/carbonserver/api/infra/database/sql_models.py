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
    public = Column(Boolean, default=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    experiments = relationship("Experiment", back_populates="project")
    organization = relationship("Organization", back_populates="projects")
    project_tokens = relationship("ProjectToken", back_populates="project")

    def __repr__(self):
        return (
            f'<Project(id="{self.id}", '
            f'name="{self.name}", '
            f'description="{self.description}", '
            f'organization_id="{self.organization_id}", '
        )


class Membership(Base):
    __tablename__ = "memberships"
    organization_id = Column(
        ForeignKey("organizations.id", ondelete="cascade"),
        primary_key=True,
    )  # ondelete='cascade'
    user_id = Column(
        ForeignKey("users.id", ondelete="cascade"),
        primary_key=True,
    )
    is_admin = Column(Boolean, nullable=False, default=False)
    organization = relationship("Organization", back_populates="users")
    user = relationship("User", back_populates="organizations")


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    projects = relationship("Project", back_populates="organization")
    users = relationship("Membership", back_populates="organization")

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
    is_active = Column(Boolean, default=True)
    organizations = relationship("Membership", back_populates="user")

    def __repr__(self):
        return (
            f'<User(id="{self.id}", '
            f'name="{self.name}", '
            f'is_active="{self.is_active}", '
            f"organizations={self.organizations}"
            f'email="{self.email}")>'
        )


class ProjectToken(Base):
    __tablename__ = "project_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String)
    hashed_token = Column(String, nullable=False)
    lookup_value = Column(
        String, nullable=False
    )  # This is the first 8 characters of the SHA-256 hash of the API key. Used for filtering faster
    revoked = Column(Boolean, default=False)
    project = relationship("Project", back_populates="project_tokens")
    # Dates
    last_used = Column(DateTime, nullable=True)
    # Permissions
    access = Column(Integer)

    def __repr__(self):
        return (
            f'<ApiKey(project_id="{self.project_id}", '
            f'hashed_token="{self.hashed_token}", '
            f'name="{self.name}", '
            f'revoked="{self.revoked}", '
            f'last_used="{self.last_used}", '
            f'access="{self.access}", '
        )
