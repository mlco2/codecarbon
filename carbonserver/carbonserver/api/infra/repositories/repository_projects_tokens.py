from contextlib import AbstractContextManager
import datetime

from dependency_injector.providers import Callable
from fastapi import HTTPException

from carbonserver.api.domain.project_tokens import ProjectTokens
from carbonserver.api.infra.api_key_utils import  generate_lookup_value,  verify_api_key
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import (
    ProjectToken as SqlModelProjectToken,
)
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import ProjectToken, ProjectTokenInternal


class SqlAlchemyRepository(ProjectTokens):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_project_token(self, project_token: ProjectTokenInternal):
        lookup_value = generate_lookup_value(project_token.token)
        with self.session_factory() as session:
            db_project_token = SqlModelProjectToken(
                project_id=project_token.project_id,
                hashed_token=project_token.hashed_token,
                expiration_date=project_token.expiration_date,
                name=project_token.name,
                access=project_token.access,
                lookup_value=lookup_value,
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
        lookup_value = generate_lookup_value(token)
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.lookup_value == lookup_value) # To be used for faster filtering
                .filter(
                    SqlModelProjectToken.project_id == project_id
                )
                .filter(verify_api_key(token, SqlModelProjectToken.hashed_token))
                .first()
            )
            if db_project_token:
                self._set_last_used(db_project_token)
                return self.map_sql_to_schema(db_project_token)
            return None

    def get_project_token_by_experiment_id_and_token(
        self, experiment_id: str, token: str
    ):
        lookup_value = generate_lookup_value(token)
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.lookup_value == lookup_value) # To be used for faster filtering
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .filter(SqlModelExperiment.id == experiment_id)
                .filter(verify_api_key(token, SqlModelProjectToken.hashed_token)) # Done last to avoid unnecessary hashing
                .first()
            )
            if db_project_token:
                self._set_last_used(db_project_token)
                return self.map_sql_to_schema(db_project_token)
            return None

    def get_project_token_by_run_id_and_token(self, run_id: str, token: str):
        lookup_value = generate_lookup_value(token)
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.lookup_value == lookup_value) # To be used for faster filtering
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .join(SqlModelRun, SqlModelExperiment.id == SqlModelRun.experiment_id)
                .filter(SqlModelRun.id == run_id)
                .filter(verify_api_key(token, SqlModelProjectToken.hashed_token)) # Done last to avoid unnecessary hashing
                .first()
            )

            if db_project_token:
                self._set_last_used(db_project_token)
                return self.map_sql_to_schema(db_project_token)
            return None

    def get_project_token_by_emission_id_and_token(self, emission_id: str, token: str):
        lookup_value = generate_lookup_value(token)
        with self.session_factory() as session:
            db_project_token = (
                session.query(SqlModelProjectToken)
                .filter(SqlModelProjectToken.lookup_value == lookup_value) # To be used for faster filtering
                .join(
                    SqlModelExperiment,
                    SqlModelProjectToken.project_id == SqlModelExperiment.project_id,
                )
                .join(SqlModelRun, SqlModelExperiment.id == SqlModelRun.experiment_id)
                .join(SqlModelEmission, SqlModelRun.id == SqlModelEmission.run_id)
                .filter(SqlModelEmission.id == emission_id)
                .filter(verify_api_key(token, SqlModelProjectToken.hashed_token)) # Done last to avoid unnecessary hashing
                .first()
            )
            if db_project_token:
                self._set_last_used(db_project_token)
                return self.map_sql_to_schema(db_project_token)
            return None
        
    def _set_last_used(self, project_token: SqlModelProjectToken):
        """Update the last_used field of the project token"""
        with self.session_factory() as session:
            project_token.last_used = datetime.datetime.now()
            session.commit()
            session.refresh(project_token)
            return self.map_sql_to_schema(project_token)

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
            last_used=project_token.last_used,
            access=project_token.access,
            expiration_date=project_token.expiration_date,
            revoked=project_token.revoked,
        )