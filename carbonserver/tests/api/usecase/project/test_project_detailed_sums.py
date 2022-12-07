from datetime import datetime
from unittest import mock

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.usecases.project.project_sum import ProjectSumsUsecase

PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"
END_DATE = datetime.now()
START_DATE = END_DATE - dateutil.relativedelta.relativedelta(months=3)


EMISSIONS_SUM = 152.28955200363455

PROJECT_WITH_DETAILS = {
    "project_id": PROJECT_ID,
    "name": "DataForGood",
    "description": "DataForGood Project",
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


def test_sum_computes_for_project_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_id = PROJECT_ID
    project_global_sum_usecase = ProjectSumsUsecase(repository_mock)

    expected_emission_sum = EMISSIONS_SUM
    repository_mock.get_project_detailed_sums.return_value = [PROJECT_WITH_DETAILS]

    actual_project_global_sum_by_experiment = (
        project_global_sum_usecase.compute_detailed_sum(
            project_id,
            START_DATE,
            END_DATE,
        )
    )

    assert (
        actual_project_global_sum_by_experiment[0]["emissions"] == expected_emission_sum
    )
