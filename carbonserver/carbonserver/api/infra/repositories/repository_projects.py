from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable
from sqlalchemy import and_, func

from carbonserver.api.domain.projects import Projects
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import Project, ProjectCreate, ProjectReport


class SqlAlchemyRepository(Projects):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_project(self, project: ProjectCreate):
        with self.session_factory() as session:
            db_project = SqlModelProject(
                name=project.name,
                description=project.description,
                team_id=project.team_id,
            )

            session.add(db_project)
            session.commit()
            session.refresh(db_project)
            return self.map_sql_to_schema(db_project)

    def get_one_project(self, project_id):
        with self.session_factory() as session:
            e = (
                session.query(SqlModelProject)
                .filter(SqlModelProject.id == project_id)
                .first()
            )
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def get_projects_from_team(self, team_id) -> List[Project]:
        """Find the list of projects from a team in database and return it

        :team_id: The id of the team to retreive projects from.
        :returns: List of Projects in pyDantic BaseModel format.
        :rtype: List[schemas.Project]
        """
        with self.session_factory() as session:
            res = session.query(SqlModelProject).filter(
                SqlModelProject.team_id == team_id
            )
            if res.first() is None:
                return []
            else:
                return [self.map_sql_to_schema(e) for e in res]

    def get_project_detailed_sums(
        self, project_id, start_date, end_date
    ) -> ProjectReport:
        """Find the experiments of a project in database between two dates and return
        a report containing the sum of their emissions

        :project_id: The id of the project to retrieve emissions from
        :start_date: the lower bound of the time interval which contains sought emissions
        :end_date: the upper bound of the time interval which contains sought emissions
        :returns: A report containing the sums of emissions
        :rtype: schemas.ProjectReport
        """
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelProject.id.label("project_id"),
                    SqlModelProject.name,
                    SqlModelProject.description,
                    func.sum(SqlModelEmission.emissions_sum).label("emissions"),
                    func.sum(SqlModelEmission.cpu_power).label("cpu_power"),
                    func.sum(SqlModelEmission.gpu_power).label("gpu_power"),
                    func.sum(SqlModelEmission.ram_power).label("ram_power"),
                    func.sum(SqlModelEmission.cpu_energy).label("cpu_energy"),
                    func.sum(SqlModelEmission.gpu_energy).label("gpu_energy"),
                    func.sum(SqlModelEmission.ram_energy).label("ram_energy"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                    func.sum(SqlModelEmission.emissions_rate).label(
                        "emissions_rate_sum"
                    ),
                    func.count(SqlModelEmission.emissions_rate).label(
                        "emissions_count"
                    ),
                )
                .join(
                    SqlModelExperiment,
                    SqlModelProject.id == SqlModelExperiment.project_id,
                    isouter=True,
                )
                .join(
                    SqlModelRun,
                    SqlModelExperiment.id == SqlModelRun.experiment_id,
                    isouter=True,
                )
                .join(
                    SqlModelEmission,
                    SqlModelRun.id == SqlModelEmission.run_id,
                    isouter=True,
                )
                .filter(SqlModelProject.id == project_id)
                .filter(
                    and_(SqlModelEmission.timestamp >= start_date),
                    (SqlModelEmission.timestamp < end_date),
                )
                .group_by(
                    SqlModelProject.id,
                    SqlModelProject.name,
                    SqlModelProject.description,
                )
                .first()
            )
            return res

    @staticmethod
    def map_sql_to_schema(project: SqlModelProject) -> Project:
        """Convert a models.Project to a schemas.Project

        :project: An Project in SQLAlchemy format.
        :returns: An Project in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        return Project(
            id=str(project.id),
            name=project.name,
            description=project.description,
            team_id=str(project.team_id),
        )
