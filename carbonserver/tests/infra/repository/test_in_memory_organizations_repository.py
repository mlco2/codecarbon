import pytest

from carbonserver.database.schemas import OrganizationCreate, Organization as SchemaOrganization
from carbonserver.database.models import Organization as ModelOrganization

from carbonserver.api.infra.repositories.repository_organization import InMemoryRepository


@pytest.fixture()
def organizations_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def organizations_fixture() -> OrganizationCreate:
    organization = OrganizationCreate.parse_obj(
        {
            "name": "1",
            "description": "Test organization"
        }
    )
    return organization


@pytest.fixture()
def model_organization() -> ModelOrganization:
    model_organization = ModelOrganization(
        **{
            "name": "1",
            "description": "Test organization"
        }

    )
    return model_organization


def test_organizations_repository_saves_correct_organization(
    organizations_repository, model_organization
):
    organization = OrganizationCreate.parse_obj(
        {
            "name": "1",
            "description": "Test organization"
        }
    )
    organizations_repository.save_organization(organization)
    saved_experiments = organizations_repository.organizations
    assert len(saved_experiments) == 1
    assert saved_experiments[0].name == "1"


def test_get_one_experiment_returns_the_correct_experiment_from_experiment_id(
    organizations_repository, organizations_fixture
):
    organization_name = "1"
    expected_experiment = SchemaOrganization.parse_obj(
        {
            "id": 1,
            "name": "1",
            "description": "Test organization"
        }
    )
    organizations_repository.save_organization(organizations_fixture)

    actual_organization = organizations_repository.get_one_organization(organization_name)
    assert expected_experiment == actual_organization


def test_get_one_experiment_returns_the_correct_experiment_list_from_experiment_id(
    organizations_repository, organizations_fixture
):
    experiment_name = "1"
    expected_emissions = [
        SchemaOrganization.parse_obj(
            {
                "id": 1,
                "name": "1",
                "description": "Test organization"
            }
        )
    ]
    organizations_repository.save_organization(organizations_fixture)

    actual_emissions = organizations_repository.get_team_from_organizations(experiment_name)

    assert expected_emissions == actual_emissions
