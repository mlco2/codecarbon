from carbonserver.config import settings
from dependency_injector import containers, providers

from carbonserver.api.infra.database.database_manager import Database
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.services.user_service import UserService


class ServerContainer(containers.DeclarativeContainer):

    config = providers.Configuration()
    db_url = settings.db_url
    db = providers.Singleton(
        Database,
        db_url=db_url,
    )
    user_repository = providers.Factory(
        SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )
