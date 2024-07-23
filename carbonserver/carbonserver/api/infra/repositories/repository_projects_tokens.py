from contextlib import AbstractContextManager

from dependency_injector.providers import Callable
from fastapi import HTTPException

from carbonserver.api.domain.project_tokens import ProjectTokens
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.infra.database.sql_models import (
    ProjectToken as SqlModelProjectToken,
)
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
                read=project_token.read,
                write=project_token.write,
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
            read=project_token.read,
            write=project_token.write,
        )
