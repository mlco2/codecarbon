import logging
from datetime import datetime
from typing import List

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.users.sql_repository import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationPatch,
    User,
)

from carbonserver.api.errors import UserException, NotAllowedError, NotAllowedErrorEnum
logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, organization_repository: OrganizationRepository, user_repository: UserRepository):
        self._organization_repository = organization_repository
        self._user_repository = user_repository

    def add_organization(self, organization: OrganizationCreate) -> Organization:
        if not self.isOperationAuthorized(organization.id, organization.user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add project to organization",
                )
            )
        else:
            created_organization: Organization = self._organization_repository.add_organization(
                organization, organization.user_id
            )
            logger.info(f"User {organization.db_user} have added org {organization.name} at {datetime.now()}")

        return created_organization

    def read_organization(self, organization_id: str, user: User) -> Organization:
        if not self.isOperationAuthorized(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add project to organization",
                )
            )
        organization: Organization = self._organization_repository.get_one_organization(
            organization_id
        )
        return organization

    def list_organizations(self, user: User = None) -> List[Organization]:
        print(user)
        return self._organization_repository.list_organizations(user=user)

    def patch_organization(
        self, organization_id: str, organization: OrganizationPatch
    ) -> Organization:
        if not self.isOperationAuthorized(organization.id, organization.user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add project to organization",
                )
            )
        updated_organization: Organization = self._organization_repository.patch_organization(
            organization_id, organization
        )
        logger.info(f"User {organization.db_user} have patched org {organization.name} at {datetime.now()}")
        return updated_organization

    def isOperationAuthorized(self, organization_id, user):
        db_user = self._user_repository.get_user_by_id(user.id)
        return organization_id in db_user.organizations
