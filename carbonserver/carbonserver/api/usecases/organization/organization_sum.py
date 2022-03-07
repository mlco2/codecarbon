from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import OrganizationReport


class OrganizationSumsUsecase:
    def __init__(self, organization_repository: SqlAlchemyRepository) -> None:
        self._organization_repository = organization_repository

    def compute_detailed_sum(
        self, organization_id: str, start_date, end_date
    ) -> OrganizationReport:
        sums = self._organization_repository.get_organization_detailed_sums(
            organization_id,
            start_date,
            end_date,
        )
        return sums
