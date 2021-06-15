from unittest import mock

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Organization, OrganizationCreate
from carbonserver.api.services.organization_service import OrganizationService

ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ORG_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_1 = Organization(
    id=ORG_ID,
    name="DFG",
    description="Data For Good Organization",
)

ORG_2 = Organization(
    id=ORG_ID_2,
    name="Data For Good",
    description="Data For Good Organization 2",
)


@mock.patch("uuid.uuid4", return_value=ORG_ID)
def test_organization_service_creates_correct_user_on_sign_up(_):

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = ORG_ID
    user_service: OrganizationService = OrganizationService(repository_mock)
    repository_mock.add_organization.return_value = ORG_1
    org_to_create = OrganizationCreate(
        name="Data For Good", description="Data For Good Organization"
    )

    actual_saved_org = user_service.add_organization(org_to_create)

    repository_mock.add_organization.assert_called_with(org_to_create)
    assert actual_saved_org.id == expected_id


def test_organiation_service_retrieves_all_existing_organizations():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org_ids_list = [ORG_ID, ORG_ID_2]
    organization_service: OrganizationService = OrganizationService(repository_mock)
    repository_mock.list_organization.return_value = [ORG_1, ORG_2]

    org_list = organization_service.list_organization()
    print(org_list[0])
    print(len(org_list))
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
