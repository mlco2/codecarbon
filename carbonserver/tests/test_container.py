from unittest import mock

from dependency_injector import providers
from dependency_injector.containers import Container

from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectSqlRepository,
)
from carbonserver.carbonserver.api.services.project_service import ProjectService


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


class TestContainer(Container):
    db = providers.Singleton(
        DatabaseMock,
        db_url=None,
    )
    projects_repository = providers.Factory(
        mock.Mock(spec=ProjectSqlRepository),
        session_factory=db.provided.session,
    )

    test_project_service = providers.Factory(
        ProjectService,
        projects_repository=projects_repository,
        auth_context=AuthContextMock(),
    )
