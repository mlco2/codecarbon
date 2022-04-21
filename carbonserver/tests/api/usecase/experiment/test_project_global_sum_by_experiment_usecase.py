from datetime import datetime
from unittest import mock

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)
from carbonserver.api.usecases.experiment.project_sum_by_experiment import (
    ProjectSumsByExperimentUsecase,
)

EXPERIMENT_ID = "10276e58-6df7-42cf-abb8-429773a35eb5"
EXPERIMENT_WITH_DETAILS_ID = "943b2aa5-9e21-41a9-8a38-562505b4b2aa"
END_DATE = datetime.now()
START_DATE = END_DATE - dateutil.relativedelta.relativedelta(months=3)


EMISSIONS_SUM = 1544.54
EMISSIONS_SUM_WITH_DETAILS = 152.28955200363455

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPERIMENT_GLOBAL_SUM = {
    "id": EXPERIMENT_ID,
    "timestamp": "2021-04-04T06:43:00",
    "name": "Run on Premise",
    "description": "Premise API for Code Carbon",
    "emission_sum": 1544.54,
    "energy_consumed": 57.21874,
    "duration": 98745,
}

EXPERIMENT_WITH_DETAILS = {
    "experiment_id": EXPERIMENT_WITH_DETAILS_ID,
    "timestamp": "2021-10-07T20:19:27.716693",
    "name": "Code Carbon user test",
    "description": "Code Carbon user test with default project",
    "country_name": "France",
    "country_iso_code": "FRA",
    "region": "france",
    "on_cloud": False,
    "cloud_provider": None,
    "cloud_region": None,
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


def test_detailed_sum_computes_for_project_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_id = PROJECT_ID
    project_global_sum_usecase = ProjectSumsByExperimentUsecase(repository_mock)

    expected_emission_sum = EMISSIONS_SUM_WITH_DETAILS
    repository_mock.get_project_detailed_sums_by_experiment.return_value = [
        EXPERIMENT_WITH_DETAILS
    ]

    actual_project_global_sum_by_experiment = (
        project_global_sum_usecase.compute_detailed_sum(
            project_id, START_DATE, END_DATE
        )
    )

    assert (
        actual_project_global_sum_by_experiment[0]["emissions"] == expected_emission_sum
    )
