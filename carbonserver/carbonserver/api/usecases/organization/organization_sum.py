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
        if sums is not None:
            return sums

        # No emissions in the requested period. Return zeros so the dashboard
        # still gets a valid report rather than a 500.
        organization = self._organization_repository.get_one_organization(
            organization_id
        )
        return OrganizationReport(
            organization_id=organization.id,
            name=organization.name,
            description=organization.description,
            emissions=0.0,
            cpu_power=0.0,
            gpu_power=0.0,
            ram_power=0.0,
            cpu_energy=0.0,
            gpu_energy=0.0,
            ram_energy=0.0,
            energy_consumed=0.0,
            duration=0,
            emissions_rate=0.0,
            emissions_count=0,
        )
