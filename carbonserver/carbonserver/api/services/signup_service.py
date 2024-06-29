from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
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
    ) -> None:
        self._user_repository: UserRepository = user_repository
        self._organization_repository: OrganizationRepository = organization_repository
        self._default_org_id = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
        self._default_api_key = "default"

    def sign_up(
        self,
        user: UserCreate,
    ) -> User:
        created_user = self._user_repository.create_user(user)
        subscribed_user = self.subscribe_user_to_org(
            created_user, self._default_org_id, self._default_api_key
        )
        print(subscribed_user)
        return subscribed_user

    def subscribe_user_to_org(
        self, user: User, organization_id: UUID, organization_api_key: str
    ):
        key_is_valid = self._organization_repository.is_api_key_valid(
            organization_id, organization_api_key
        )
        if key_is_valid:
            self._user_repository.subscribe_user_to_org(user, organization_id)
        return user
