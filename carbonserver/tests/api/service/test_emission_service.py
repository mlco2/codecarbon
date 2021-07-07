from unittest import mock

from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Emission, EmissionCreate
from carbonserver.api.services.emissions_service import EmissionService

RUN_1_ID = "40088f1a-d28e-4980-8d80-bf5600056a14"
RUN_2_ID = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_3 = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_1 = Emission(
    id=EMISSION_ID,
    timestamp="2021-04-04T08:43:00+02:00",
    run_id=RUN_1_ID,
    duration=98745,
    emissions=1.548444,
    energy_consumed=57.21874,
    cpu_power=57.21874,
    gpu_power=0.0
)

EMISSION_2 = Emission(
    id=EMISSION_ID_2,
    timestamp="2021-04-04T08:43:00+02:00",
    run_id=RUN_1_ID,
    duration=98745,
    emissions=1.548444,
    energy_consumed=57.21874,
    cpu_power=57.21874,
    gpu_power=0.0
)

EMISSION_3 = Emission(
    id=EMISSION_ID_3,
    timestamp="2021-04-04T08:43:00+02:00",
    run_id=RUN_1_ID,
    duration=98745,
    emissions=1.548444,
    energy_consumed=57.21874,
    cpu_power=57.21874,
    gpu_power=0.0
)


@mock.patch("uuid.uuid4", return_value=EMISSION_ID)
def test_emission_service_creates_correct_emission(_):
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = EMISSION_ID
    emission_service: EmissionService = EmissionService(repository_mock)
    repository_mock.add_emission.return_value = EMISSION_ID

    emission_to_create = EmissionCreate(
        timestamp="2021-04-04T08:43:00+02:00",
        run_id=RUN_1_ID,
        duration=98745,
        emissions=1.548444,
        energy_consumed=57.21874,
        cpu_power=57.21874,
        gpu_power=0.0
    )

    actual_saved_emission_id = emission_service.add_emission(emission_to_create)

    assert actual_saved_emission_id == expected_id


def test_emission_service_retrieves_all_existing_emissions_for_one_run():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_emissions_ids = [EMISSION_1.id, EMISSION_2.id]
    emission_service: EmissionService = EmissionService(repository_mock)
    repository_mock.get_emissions_from_run.return_value = [EMISSION_1, EMISSION_2]

    emissions_list = emission_service.get_emissions_from_run(RUN_1_ID)
    actual_emissions_ids_list = map(lambda x: x.id, iter(emissions_list))
    diff = set(actual_emissions_ids_list) ^ set(expected_emissions_ids)

    assert not diff
    assert len(list(actual_emissions_ids_list)) == len(set(actual_emissions_ids_list))


def test_emission_service_retrives_correct_emission_by_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission_id = EMISSION_1.id
    emission_service: EmissionService = EmissionService(repository_mock)
    repository_mock.get_one_emission.return_value = EMISSION_1

    actual_emission = emission_service.get_one_emission(EMISSION_ID)

    assert actual_emission.id == expected_emission_id
