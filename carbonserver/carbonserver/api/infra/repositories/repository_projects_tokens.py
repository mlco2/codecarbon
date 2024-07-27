from contextlib import AbstractContextManager

from dependency_injector.providers import Callable
from fastapi import HTTPException

from carbonserver.api.domain.project_tokens import ProjectTokens
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import (
    ProjectToken as SqlModelProjectToken,
)
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import ProjectToken, ProjectTokenCreate


class SqlAlchemyRepository(ProjectTokens):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_project_token(self, project_id: str, project_token: ProjectTokenCreate):
        token = f"pt_{generate_api_key()}"  # pt stands for project token
        with self.session_factory() as session:
            db_project_token = SqlModelProjectToken(
                project_id=project_id,
                token=token,
                name=project_token.name,
                access=project_token.access,
            )
            session.add(db_project_token)
            session.commit()
            session.refresh(db_project_token)
            return self.map_sql_to_schema(db_project_token)

    def delete_project_token(self, project_id: str, token_id: str):
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(
                    SqlModelProjectToken.id == token_id
                    and SqlModelProjectToken.project_id == project_id
                )
                .first()
            )
            if db_project_token is None:
                raise HTTPException(
                    status_code=404, detail=f"Project token {token_id} not found"
                )
            session.delete(db_project_token)
            session.commit()

    def list_project_tokens(self, project_id: str):
        with self.session_factory() as session:
            db_project_tokens = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.project_id == project_id)
                .all()
            )
            return [
                self.map_sql_to_schema(project_token)
                for project_token in db_project_tokens
            ]

    def get_project_token_by_project_id_and_token(self, project_id: str, token: str):
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(
                    SqlModelProjectToken.project_id == project_id
                    and SqlModelProjectToken.token == token
                )
                .first()
            )
            if db_project_token is None:
                raise HTTPException(status_code=404, detail="Project token not found")
            return self.map_sql_to_schema(db_project_token)

    def get_project_token_by_experiment_id_and_token(
        self, experiment_id: str, token: str
    ):
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.token == token)
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .filter(SqlModelExperiment.id == experiment_id)
                .first()
            )
            if db_project_token is None:
                raise HTTPException(status_code=404, detail="Project token not found")
            return self.map_sql_to_schema(db_project_token)

    def get_project_token_by_run_id_and_token(self, run_id: str, token: str):
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.token == token)
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .join(SqlModelRun, SqlModelExperiment.id == SqlModelRun.experiment_id)
                .filter(SqlModelRun.id == run_id)
                .first()
            )
            if db_project_token is None:
                raise HTTPException(status_code=404, detail="Project token not found")
            return self.map_sql_to_schema(db_project_token)

    def get_project_token_by_emission_id_and_token(self, emission_id: str, token: str):
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.token == token)
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .join(SqlModelRun, SqlModelExperiment.id == SqlModelRun.experiment_id)
                .join(SqlModelEmission, SqlModelRun.id == SqlModelEmission.run_id)
                .filter(SqlModelEmission.id == emission_id)
                .first()
            )
            if db_project_token is None:
                raise HTTPException(status_code=404, detail="Project token not found")
            return self.map_sql_to_schema(db_project_token)

    @staticmethod
    def map_sql_to_schema(project_token: SqlModelProjectToken) -> ProjectToken:
        """Convert a models.ProjectToken to a schemas.ProjectToken

        :project: An ProjectToken in SQLAlchemy format.
        :returns: An ProjectToken in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        return ProjectToken(
            id=str(project_token.id),
            name=project_token.name,
            project_id=project_token.project_id,
            token=project_token.token,
            last_used=project_token.last_used,
            access=project_token.access,
        )
