from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import OrganizationReport
from carbonserver.api.services.auth_context import AuthContext


class OrganizationSumsUsecase:
    def __init__(
        self, organization_repository: SqlAlchemyRepository, auth_context: AuthContext
    ) -> None:
        self._organization_repository = organization_repository
        self._auth_context = auth_context

    def compute_detailed_sum(
        self, organization_id: str, start_date, end_date, user=None
    ) -> OrganizationReport:
        if not self._auth_context.can_read_organization(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
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
