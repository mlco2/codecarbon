from typing import List

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
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
        self, organization_repository: SqlAlchemyRepository, auth_context: AuthContext
    ):
        self._repository = organization_repository
        self._auth_context = auth_context

    def add_organization(self, organization: OrganizationCreate) -> Organization:
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
