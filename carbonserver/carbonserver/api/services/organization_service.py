from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Organization, OrganizationCreate


class OrganizationService:
    def __init__(self, organization_repository: SqlAlchemyRepository):
        self._repository = organization_repository

    def add_organization(self, organization: OrganizationCreate) -> Organization:

        created_organization = self._repository.add_organization(organization)
        return created_organization

    def read_organization(self, organization_id: str) -> Organization:

        return self._repository.get_one_organization(organization_id)

    def list_organization(self):

        return self._repository.list_organization()
