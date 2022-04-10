from datetime import datetime
from unittest import mock

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.usecases.run.experiment_sum_by_run import (
    ExperimentSumsByRunUsecase,
)

EXPERIMENT_ID = "2916fe6c-00a0-40b6-a3bd-ae9877661bdb"
END_DATE = datetime.now()
START_DATE = END_DATE - dateutil.relativedelta.relativedelta(months=3)

EMISSIONS_SUM = 152.28955200363455

EXPERIMENT_WITH_DETAILS = {
    "run_id": EXPERIMENT_ID,
    "timestamp": "2022-03-16T21:57:41.003455",
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
    "emissions_rate_count": 64,
}


def test_detailed_sum_computes_for_experiment_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    experiment_id = EXPERIMENT_ID
    experiment_sum_by_run_usecase = ExperimentSumsByRunUsecase(repository_mock)

    expected_emission_sum = EMISSIONS_SUM
    repository_mock.get_experiment_detailed_sums_by_run.return_value = [
        EXPERIMENT_WITH_DETAILS
    ]

    actual_experiment_sum_by_run = experiment_sum_by_run_usecase.compute_detailed_sum(
        experiment_id, START_DATE, END_DATE
    )

    assert actual_experiment_sum_by_run[0]["emissions"] == expected_emission_sum
