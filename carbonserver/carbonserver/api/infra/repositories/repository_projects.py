from contextlib import AbstractContextManager

from dependency_injector.providers import Callable

from carbonserver.api.domain.projects import Projects
from carbonserver.api.schemas import Project, ProjectCreate
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject


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
            return db_project

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
