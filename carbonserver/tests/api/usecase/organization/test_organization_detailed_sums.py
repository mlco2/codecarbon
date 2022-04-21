from datetime import datetime
from unittest import mock

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
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
    "emissions_rate_sum": 1.0984556074701752,
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
