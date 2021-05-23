from typing import Optional

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_teams import (
    SqlAlchemyRepository as TeamRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import OrganizationCreate, TeamCreate, User, UserCreate


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

    def sign_up(
        self,
        user: UserCreate,
        organization: Optional[OrganizationCreate],
        team: Optional[TeamCreate],
    ) -> User:
        self._organization_repository.add_organization(organization)
        # TODO : add team from org_id
        self._team_repository.add_team(team)
        # TODO : add user with org / team id
        created_user = self._user_repository.create_user(user)

        return created_user
