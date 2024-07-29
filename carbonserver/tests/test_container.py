from dependency_injector import containers, providers
from fastapi import FastAPI

from carbonserver.carbonserver.api.auth_middleware import OAuthHTTPMiddleware
from carbonserver.carbonserver.api.infra.database.database_manager import Database
from carbonserver.carbonserver.api.infra.repositories.users.inmemory_repositry import InMemoryRepository
from carbonserver.carbonserver.config import settings

test_app = FastAPI()


class TestContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_url = settings.db_url
    db = providers.Singleton(
        Database,
        db_url=db_url,
    )

    users_repository = providers.Factory(
        InMemoryRepository
    )

