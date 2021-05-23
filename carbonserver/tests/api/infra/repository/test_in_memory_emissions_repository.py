import pytest

from carbonserver.api.infra.repositories.repository_emissions import InMemoryRepository
from carbonserver.api.schemas import Emission as SchemaEmission
from carbonserver.api.schemas import EmissionCreate
from carbonserver.database.sql_models import Emission as ModelEmission


@pytest.fixture()
def emissions_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def emission_fixture() -> EmissionCreate:
    emission = EmissionCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        }
    )
    return emission


@pytest.fixture()
def model_emission() -> ModelEmission:
    model_emission = ModelEmission(
        **{
            "id": 1,
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        }
    )
    return model_emission


def test_emissions_repository_saves_correct_emission(
    emissions_repository, model_emission
):
    emission = EmissionCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        }
    )
    emissions_repository.add_emission(emission)
    saved_emissions = emissions_repository.emissions

    assert len(saved_emissions) == 1
    assert saved_emissions[0].id == model_emission.id


def test_emissions_repository_get_db_to_class_returns_correct_object_type(
    emissions_repository, model_emission
):
    expected_schema_emission = SchemaEmission.parse_obj(
        {
            "id": 1,
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        }
    )

    actual_schema_emission = emissions_repository.get_db_to_class(model_emission)

    assert expected_schema_emission == actual_schema_emission


def test_get_one_emission_returns_the_correct_emission_from_emission_id(
    emissions_repository, emission_fixture
):
    emission_id = 1
    expected_emission = SchemaEmission.parse_obj(
        {
            "id": 1,
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        }
    )
    emissions_repository.add_emission(emission_fixture)

    actual_emission = emissions_repository.get_one_emission(emission_id)

    assert expected_emission == actual_emission


def test_get_one_emission_returns_the_correct_emission_list_from_experiment_id(
    emissions_repository, emission_fixture
):
    run_id = "40088f1a-d28e-4980-8d80-bf5600056a14"
    expected_emissions = [
        SchemaEmission.parse_obj(
            {
                "id": 1,
                "timestamp": "2021-04-04T08:43:00+02:00",
                "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
                "duration": 98745,
                "emissions": 1.548444,
                "energy_consumed": 57.21874,
            }
        )
    ]
    emissions_repository.add_emission(emission_fixture)

    actual_emissions = emissions_repository.get_emissions_from_run(run_id)

    assert expected_emissions == actual_emissions
