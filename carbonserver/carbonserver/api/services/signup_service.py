from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_teams import (
    SqlAlchemyRepository as TeamRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import User, UserCreate


class SignUpService:
    def __init__(
        self,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        team_repository: TeamRepository,
    ) -> None:
        self._user_repository: UserRepository = user_repository
        self._organization_repository: OrganizationRepository = organization_repository
        self._team_repository: TeamRepository = team_repository
        self._default_org_id = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
        self._default_team_id = UUID("8edb03e1-9a28-452a-9c93-a3b6560136d7")
        self._default_api_key = "default"

    def sign_up(
        self,
        user: UserCreate,
    ) -> User:
        created_user = self._user_repository.create_user(user)
        self.subscribe_user_to_org(
            created_user,
            self._default_org_id,
            self._default_api_key,
        )
        subscribed_user = self.subscribe_user_to_team(
            created_user,
            self._default_team_id,
            self._default_api_key,
        )
        print(subscribed_user)
        return subscribed_user

    def subscribe_user_to_org(
        self,
        user: User,
        organization_id: UUID,
        organization_api_key: str,
    ):
        key_is_valid = self._organization_repository.is_api_key_valid(
            organization_id,
            organization_api_key,
        )
        if key_is_valid:
            self._user_repository.subscribe_user_to_org(user, organization_id)
        return user

    def subscribe_user_to_team(self, user: User, team_id: UUID, team_api_key: str):
        key_is_valid = self._team_repository.is_api_key_valid(team_id, team_api_key)
        if key_is_valid:
            self._user_repository.subscribe_user_to_team(user, team_id)
        print(user)
        return user
