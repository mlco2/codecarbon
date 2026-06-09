from datetime import datetime
from unittest import mock
from uuid import UUID

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Organization
from carbonserver.api.usecases.organization.organization_sum import (
    OrganizationSumsUsecase,
)

ORG_ID = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
END_DATE = datetime.now()
START_DATE = END_DATE - dateutil.relativedelta.relativedelta(months=3)


EMISSIONS_SUM = 152.28955200363455

ORG_WITH_DETAILS = {
    "organization_id": ORG_ID,
    "name": "DataForGood",
    "description": "DataForGood",
    "emissions": 152.28955200363455,
    "cpu_power": 5760,
    "gpu_power": 2983.9739999999993,
    "ram_power": 806.0337192959997,
    "cpu_energy": 191.8251863024175,
    "gpu_energy": 140.01098718681496,
    "ram_energy": 26.84332784201141,
    "energy_consumed": 358.6795013312438,
    "duration": 7673204,
    "emissions_rate": 1.0984556074701752,
    "emissions_count": 64,
}


def test_sum_computes_for_organization_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    organization_id = ORG_ID
    organization_global_sum_usecase = OrganizationSumsUsecase(repository_mock)

    expected_emission_sum = EMISSIONS_SUM
    repository_mock.get_organization_detailed_sums.return_value = [ORG_WITH_DETAILS]

    actual_organization_global_sum_by_experiment = (
        organization_global_sum_usecase.compute_detailed_sum(
            organization_id, START_DATE, END_DATE
        )
    )

    assert (
        actual_organization_global_sum_by_experiment[0]["emissions"]
        == expected_emission_sum
    )


def test_sum_returns_zero_report_when_organization_has_no_emissions():
    """Issue #693: an organization with no emissions in the requested period
    should get back a zero-valued report instead of triggering the global
    "Generic error" handler.
    """
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.get_organization_detailed_sums.return_value = None
    repository_mock.get_one_organization.return_value = Organization(
        id=UUID(ORG_ID),
        name="Quiet Org",
        description="An organization that has not logged anything yet.",
    )
    usecase = OrganizationSumsUsecase(repository_mock)

    report = usecase.compute_detailed_sum(ORG_ID, START_DATE, END_DATE)

    assert report.organization_id == UUID(ORG_ID)
    assert report.name == "Quiet Org"
    assert report.emissions == 0.0
    assert report.energy_consumed == 0.0
    assert report.duration == 0
    assert report.emissions_count == 0
