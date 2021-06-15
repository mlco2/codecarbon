import pytest

from carbonserver.api.infra.repositories.repository_organizations import (
    InMemoryRepository,
)
from carbonserver.api.schemas import Organization as SchemaOrganization
from carbonserver.api.schemas import OrganizationCreate
from carbonserver.database.sql_models import Organization as ModelOrganization


@pytest.fixture()
def organizations_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def organizations_fixture() -> OrganizationCreate:
    organization = OrganizationCreate.parse_obj(
        {"name": "1", "description": "Test organization"}
    )
    return organization


@pytest.fixture()
def model_organization() -> ModelOrganization:
    model_organization = ModelOrganization(
        **{"name": "1", "description": "Test organization"}
    )
    return model_organization


def test_organizations_repository_saves_correct_organization(
    organizations_repository, model_organization
):
    organization = OrganizationCreate.parse_obj(
        {"name": "1", "description": "Test organization"}
    )
    organizations_repository.add_organization(organization)
    saved_experiments = organizations_repository.organizations
    assert len(saved_experiments) == 1
    assert saved_experiments[0].name == "1"


def test_get_one_organization_returns_the_correct_organization_from_organization_name(
    organizations_repository, organizations_fixture
):
    organization_name = "1"
    expected_organization = SchemaOrganization.parse_obj(
        {"id": 1, "name": "1", "description": "Test organization"}
    )
    organizations_repository.add_organization(organizations_fixture)

    actual_organization = organizations_repository.get_one_organization(
        organization_name
    )
    assert expected_organization == actual_organization


def test_get_one_organization_returns_the_correct_organizations_list_from_organization_name(
    organizations_repository, organizations_fixture
):
    organization_name = "1"
    expected_organizations = [
        SchemaOrganization.parse_obj(
            {"id": 1, "name": "1", "description": "Test organization"}
        )
    ]
    organizations_repository.add_organization(organizations_fixture)

    actual_organizations = organizations_repository.list_organization(organization_name)

    assert expected_organizations == actual_organizations
