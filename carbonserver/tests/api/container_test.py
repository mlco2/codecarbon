from dependency_injector import containers, providers

from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectSqlRepository,
)
from carbonserver.api.services.project_service import ProjectService


class DatabaseMock:
    def __init__(self, db_url):
        self.db_url = db_url


class AuthContextMock:
    @staticmethod
    def isOperationAuthorizedOnOrg():
        return True

    @staticmethod
    def isOperationAuthorizedOnProject():
        return True


class FakeContainer(containers.DeclarativeContainer):
    db = providers.Singleton(
        DatabaseMock,
        db_url=None,
    )
    projects_repository = providers.Factory(
        ProjectSqlRepository,
        session_factory=db.provided.session,
    )

    project_service = providers.Factory(
        ProjectService,
        projects_repository=projects_repository,
        auth_context=AuthContextMock(),
    )
