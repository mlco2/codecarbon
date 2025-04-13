from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable
from sqlalchemy import Text, and_, cast, func

from carbonserver.api.domain.projects import Projects
from carbonserver.api.errors import NotFoundError, NotFoundErrorEnum, UserException
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
                organization_id=project.organization_id,
            )

            session.add(db_project)
            session.commit()
            session.refresh(db_project)
            return self.map_sql_to_schema(db_project)

    def delete_project(self, project_id: str) -> None:
        with self.session_factory() as session:
            db_project = (
                session.query(SqlModelProject)
                .filter(SqlModelProject.id == project_id)
                .first()
            )
            if db_project is None:
                raise UserException(
                    NotFoundError(
                        code=NotFoundErrorEnum.NOT_FOUND,
                        message=f"Project not found: {project_id}",
                    )
                )
            session.delete(db_project)
            session.commit()

    def get_one_project(self, project_id) -> Project:
        with self.session_factory() as session:
            e = (
                session.query(SqlModelProject)
                .filter(SqlModelProject.id == project_id)
                .first()
            )
            if e is None:
                raise UserException(
                    NotFoundError(
                        code=NotFoundErrorEnum.NOT_FOUND,
                        message=f"Project not found: {project_id}",
                    )
                )
            experiments = (
                session.query(cast(SqlModelExperiment.id, Text))
                .filter(SqlModelExperiment.project_id == project_id)
                .all()
            )
            project = self.map_sql_to_schema(e)
            project.experiments = [experiment[0] for experiment in experiments]
            return project

    def is_project_public(self, project_id) -> bool:
        with self.session_factory() as session:
            db_project = (
                session.query(SqlModelProject)
                .filter(SqlModelProject.id == project_id)
                .first()
            )
            if db_project is None:
                raise UserException(
                    NotFoundError(
                        code=NotFoundErrorEnum.NOT_FOUND,
                        message=f"Project not found: {project_id}",
                    )
                )
            return db_project.public

    def get_projects_from_organization(self, organization_id) -> List[Project]:
        """Find the list of projects from a organization in database and return it

        :org_id: The id of the organization to retreive projects from.
        :returns: List of Projects in pyDantic BaseModel format.
        :rtype: List[schemas.Project]
        """
        with self.session_factory() as session:
            res = session.query(SqlModelProject).filter(
                SqlModelProject.organization_id == organization_id
            )
            if res.first() is None:
                return []
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
                    SqlModelProject.organization_id,
                    func.sum(SqlModelEmission.emissions_sum).label("emissions"),
                    func.avg(SqlModelEmission.cpu_power).label("cpu_power"),
                    func.avg(SqlModelEmission.gpu_power).label("gpu_power"),
                    func.avg(SqlModelEmission.ram_power).label("ram_power"),
                    func.sum(SqlModelEmission.cpu_energy).label("cpu_energy"),
                    func.sum(SqlModelEmission.gpu_energy).label("gpu_energy"),
                    func.sum(SqlModelEmission.ram_energy).label("ram_energy"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                    func.avg(SqlModelEmission.emissions_rate).label("emissions_rate"),
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
                    (SqlModelEmission.timestamp <= end_date),
                )
                .group_by(
                    SqlModelProject.id,
                    SqlModelProject.name,
                    SqlModelProject.description,
                )
                .first()
            )
            return res

    def patch_project(self, project_id, project) -> Project:
        with self.session_factory() as session:
            db_project = (
                session.query(SqlModelProject)
                .filter(SqlModelProject.id == project_id)
                .first()
            )
            if db_project is None:
                raise UserException(
                    NotFoundError(
                        code=NotFoundErrorEnum.NOT_FOUND,
                        message=f"Project not found: {project_id}",
                    )
                )
            for attr, value in project.dict().items():
                if value is not None:
                    setattr(db_project, attr, value)
            session.commit()
            session.refresh(db_project)
            return self.map_sql_to_schema(db_project)

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
            public=project.public,
            organization_id=str(project.organization_id),
        )
