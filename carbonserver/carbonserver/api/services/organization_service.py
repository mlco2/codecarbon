from typing import List
from uuid import UUID

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationPatch,
    User,
)
from carbonserver.api.services.auth_context import AuthContext


class OrganizationService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        auth_context: AuthContext,
    ):
        self._user_repository: UserRepository = user_repository
        self._repository: OrganizationRepository = organization_repository
        self._auth_context = auth_context

    def add_organization(
        self, organization: OrganizationCreate, user: User = None
    ) -> Organization:
        created_organization: Organization = self._repository.add_organization(
            organization
        )
        return created_organization

    def read_organization(self, organization_id: str, user: User) -> Organization:
        if not self._auth_context.isOperationAuthorizedOnOrg(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Operation not authorized on organization",
                )
            )
        else:
            organization: Organization = self._repository.get_one_organization(
                organization_id
            )
            return organization

    def list_organizations(self, user: User = None) -> List[Organization]:
        return self._repository.list_organizations(user=user)

    def list_users(
        self, organization_id: UUID | str, user: User = None
    ) -> List[Organization]:
        # TODO: check permission
        # if not self._auth_context.can_read_organization(organization_id, user):
        #     raise UserException(
        #         NotAllowedError(
        #             code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
        #             message="Operation not authorized on organization",
        #         )
        #     )
        return self._repository.list_users(organization_id=organization_id)

    def patch_organization(
        self, organization_id: str, organization: OrganizationPatch, user: User
    ) -> Organization:
        if not self._auth_context.isOperationAuthorizedOnOrg(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Operation not authorized on organization",
                )
            )
        else:
            updated_organization: Organization = self._repository.patch_organization(
                organization_id, organization
            )
            return updated_organization

    def add_user_by_mail(self, *, organization_id: str, email: str, user: User = None):
        # TODO: check permissions ; user must be admin on organization
        user_to_add = self._user_repository.get_user_by_email(email=email)
        return self._user_repository.subscribe_user_to_org(
            user=user_to_add, organization_id=organization_id
        )
