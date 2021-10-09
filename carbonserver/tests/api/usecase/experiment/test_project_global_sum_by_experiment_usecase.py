from unittest import mock

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)
from carbonserver.api.usecases.experiment.project_global_sum_by_experiment import (
    ProjectGlobalSumsByExperimentUsecase,
)

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPERIMENT_GLOBAL_SUM = {
    "id": "10276e58-6df7-42cf-abb8-429773a35eb5",
    "timestamp": "2021-04-04T06:43:00",
    "name": "Run on Premise",
    "description": "Premise API for Code Carbon",
    "emission_sum": 1544.54,
    "energy_consumed": 57.21874,
    "duration": 98745,
}


def test_global_sum_computes_for_project_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_id = PROJECT_ID
    project_global_sum_usecase = ProjectGlobalSumsByExperimentUsecase(repository_mock)
    expected_emission_sum = 1544.54
    repository_mock.get_project_global_sums_by_experiment.return_value = [
        EXPERIMENT_GLOBAL_SUM
    ]

    actual_project_global_sum_by_experiment = project_global_sum_usecase.compute(
        project_id
    )

    assert actual_project_global_sum_by_experiment.emission_sum == expected_emission_sum
