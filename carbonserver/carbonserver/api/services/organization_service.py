from typing import List

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Organization, OrganizationCreate


class OrganizationService:
    def __init__(self, organization_repository: SqlAlchemyRepository):
        self._repository = organization_repository

    def add_organization(self, organization: OrganizationCreate) -> Organization:
        created_organization: Organization = self._repository.add_organization(
            organization
        )

        return created_organization

    def read_organization(self, organization_id: str) -> Organization:
        organization: Organization = self._repository.get_one_organization(
            organization_id
        )

        return organization

    def list_organizations(self) -> List[Organization]:
        organizations: List[Organization] = self._repository.list_organizations()

        return organizations
