from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Organization, OrganizationCreate
from carbonserver.api.services.organization_service import OrganizationService

ORG_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"

ORG_1 = Organization(
    id=ORG_ID, name="DFG", description="Data For Good Organization", api_key=API_KEY
)

ORG_2 = Organization(
    id=ORG_ID_2,
    name="Data For Good",
    description="Data For Good Organization 2",
    api_key=API_KEY,
)


@mock.patch("uuid.uuid4", return_value=ORG_ID)
def test_organization_service_add_org_creates_correct_org(_):

    expected_id = ORG_ID
    expected_api_key = API_KEY
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.add_organization.return_value = ORG_1

    user_service: OrganizationService = OrganizationService(repository_mock)
    org_to_create = OrganizationCreate(
        name="Data For Good", description="Data For Good Organization"
    )

    actual_saved_org = user_service.add_organization(org_to_create)

    repository_mock.add_organization.assert_called_with(org_to_create)
    assert actual_saved_org.id == expected_id
    assert actual_saved_org.api_key == expected_api_key


def test_organiation_service_retrieves_all_existing_organizations():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org_ids_list = [ORG_ID, ORG_ID_2]
    organization_service: OrganizationService = OrganizationService(repository_mock)
    repository_mock.list_organizations.return_value = [ORG_1, ORG_2]

    org_list = organization_service.list_organizations()
    actual_user_ids_list = map(lambda x: x.id, iter(org_list))
    diff = set(actual_user_ids_list) ^ set(expected_org_ids_list)

    assert not diff
    assert len(org_list) == len(expected_org_ids_list)


def test_organization_service_retrieves_correct_org_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org: Organization = ORG_1
    organization_service: OrganizationService = OrganizationService(repository_mock)
    repository_mock.get_one_organization.return_value = ORG_1

    actual_saved_org = organization_service.read_organization(ORG_ID)

    assert actual_saved_org.id == expected_org.id
    assert actual_saved_org.name == expected_org.name
