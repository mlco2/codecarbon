"""create tables

Revision ID: b7037ddec60c
Revises:
Create Date: 2021-05-09 08:44:29.554956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7037ddec60c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "emissions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("duration", sa.Float),
        sa.Column("emissions", sa.Float),
        sa.Column("energy_consumed", sa.Float),
        # run_id = sa.Column('', Integer, ForeignKey("runs.id"),),
        # run = relationship("Run", back_populates="emissions"),
    )


# class Run(Base),:
#     __tablename__ = "runs"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     timestamp = sa.Column('', sa.DateTime),
#     experiment_id = sa.Column('', Integer, ForeignKey("experiments.id"),),
#     experiment = relationship("Experiment", back_populates="runs"),
#     # emission_id = sa.Column('', Integer,ForeignKey("emissions.id"),),
#     emissions = relationship("Emission", back_populates="run"),


# # Un experiment = un run
# class Experiment(Base),:
#     __tablename__ = "experiments"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     timestamp = sa.Column('', sa.DateTime),
#     name = sa.Column('', sa.String),
#     description = sa.Column('', sa.String),
#     is_active = sa.Column('', Boolean, default=True),
#     ########################
#     country_name = sa.Column('', sa.String),
#     country_iso_code = sa.Column('', sa.String),
#     region = sa.Column('', sa.String),
#     on_cloud = sa.Column('', Boolean, default=False),
#     cloud_provider = sa.Column('', sa.String),
#     cloud_region = sa.Column('', sa.String),
#     # emission_id = sa.Column('', Integer,ForeignKey("emission.id"),),
#     project_id = sa.Column('', Integer, ForeignKey("projects.id"),),
#     #########################
#     # emissions = relationship("Emission", back_populates="experiment"),
#     project = relationship("Project", back_populates="experiments"),
#     runs = relationship("Run", back_populates="experiment"),


# class Project(Base),:
#     __tablename__ = "projects"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     name = sa.Column('', sa.String),
#     description = sa.Column('', sa.String),
#     team_id = sa.Column('', Integer, ForeignKey("teams.id"),),
#     experiments = relationship("Experiment", back_populates="project"),
#     team = relationship("Team", back_populates="projects"),


# class Team(Base),:
#     __tablename__ = "teams"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     name = sa.Column('', sa.String),
#     description = sa.Column('', sa.String),
#     organization_id = sa.Column('', Integer, ForeignKey("organizations.id"),),
#     projects = relationship("Project", back_populates="team"),
#     organization = relationship("Organization", back_populates="teams"),


# # Organization
# class Organization(Base),:
#     __tablename__ = "organizations"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     name = sa.Column('', sa.String),
#     description = sa.Column('', sa.String),
#     teams = relationship("Team", back_populates="organization"),


# class User(Base),:
#     __tablename__ = "users"

#     id = sa.Column('', Integer, primary_key=True, index=True),
#     name = sa.Column('', sa.String),
#     email = sa.Column('', sa.String, unique=True, index=True),
#     hashed_password = sa.Column('', sa.String),
#     is_active = sa.Column('', Boolean, default=True),


def downgrade():
    tables = [
        "emissions",
        "runs",
        "experiments",
        "projects",
        "teams",
        "organizations",
        "users",
    ]
    for t in tables:
        op.drop_table(t)
