from dependency_injector import containers, providers

from carbonserver.api.infra.database.database_manager import Database
from carbonserver.api.infra.repositories import (
    repository_organizations,
    repository_teams,
    repository_users,
)
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService
from carbonserver.config import settings


class ServerContainer(containers.DeclarativeContainer):

    config = providers.Configuration()
    db_url = settings.db_url
    db = providers.Singleton(
        Database,
        db_url=db_url,
    )
    user_repository = providers.Factory(
        repository_users.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    organization_repository = providers.Factory(
        repository_organizations.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    team_repository = providers.Factory(
        repository_teams.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )

    sign_up = providers.Factory(
        SignUpService,
        user_repository=user_repository,
        organization_repository=organization_repository,
        team_repository=team_repository,
    )
