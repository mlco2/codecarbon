from typing import List
from unittest import mock
from uuid import UUID

from api.mocks import DUMMY_USER, FakeAuthContext

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationPatch,
    OrganizationUser,
)
from carbonserver.api.services.organization_service import OrganizationService

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"

ORG_1 = Organization(id=ORG_ID, name="DFG", description="Data For Good Organization")

ORG_2 = Organization(
    id=ORG_ID_2,
    name="Data For Good",
    description="Data For Good Organization 2",
)

ORG_USER = OrganizationUser(
    id=USER_ID_1,
    name="user1",
    email="user1@local.com",
    is_active=True,
    organization_id=ORG_1.id,
    is_admin=True,
)


@mock.patch("uuid.uuid4", return_value=ORG_ID)
def test_organization_service_add_org_creates_correct_org(_):
    expected_id = ORG_ID
    repository_mock: OrganizationRepository = mock.Mock(spec=OrganizationRepository)
    repository_mock.add_organization.return_value = ORG_1
    user_repository_mock: UserRepository = mock.Mock(spec=UserRepository)

    org_service: OrganizationService = OrganizationService(
        user_repository=user_repository_mock,
        organization_repository=repository_mock,
        auth_context=FakeAuthContext(),
    )
    org_to_create = OrganizationCreate(
        name="Data For Good", description="Data For Good Organization"
    )

    actual_saved_org = org_service.add_organization(org_to_create, ORG_USER)

    repository_mock.add_organization.assert_called_with(org_to_create)
    assert actual_saved_org.id == expected_id


def test_organiation_service_retrieves_all_existing_organizations():
    expected_org_ids_list = [ORG_ID, ORG_ID_2]
    repository_mock: OrganizationRepository = mock.Mock(spec=OrganizationRepository)
    user_repository_mock: UserRepository = mock.Mock(spec=UserRepository)
    organization_service: OrganizationService = OrganizationService(
        user_repository=user_repository_mock,
        organization_repository=repository_mock,
        auth_context=FakeAuthContext(),
    )
    repository_mock.list_organizations.return_value = [ORG_1, ORG_2]

    org_list = organization_service.list_organizations()
    actual_org_ids_list = map(lambda x: x.id, iter(org_list))
    diff = set(actual_org_ids_list) ^ set(expected_org_ids_list)

    assert not diff
    assert len(org_list) == len(expected_org_ids_list)


def test_organization_service_retrieves_correct_org_by_id():
    expected_org: Organization = ORG_1
    repository_mock: OrganizationRepository = mock.Mock(spec=OrganizationRepository)
    user_repository_mock: UserRepository = mock.Mock(spec=UserRepository)
    organization_service: OrganizationService = OrganizationService(
        user_repository=user_repository_mock,
        organization_repository=repository_mock,
        auth_context=FakeAuthContext(),
    )
    repository_mock.get_one_organization.return_value = ORG_1

    actual_saved_org = organization_service.read_organization(ORG_ID, DUMMY_USER)

    assert actual_saved_org.id == expected_org.id
    assert actual_saved_org.name == expected_org.name


def test_organization_service_patches_correct_org():
    repository_mock: OrganizationRepository = mock.Mock(spec=OrganizationRepository)
    user_repository_mock: UserRepository = mock.Mock(spec=UserRepository)
    organization_service: OrganizationService = OrganizationService(
        user_repository=user_repository_mock,
        organization_repository=repository_mock,
        auth_context=FakeAuthContext(),
    )
    patched_org = Organization(
        id=ORG_2.id,
        name="PATCHED - Data For Good",
        description="PATCHED - Data For Good Organization",
    )
    repository_mock.patch_organization.return_value = patched_org

    org_to_patch = OrganizationPatch(
        name="PATCHED - Data For Good",
        description="PATCHED - Data For Good Organization",
    )

    actual_saved_org = organization_service.patch_organization(
        ORG_ID_2, org_to_patch, DUMMY_USER
    )

    assert actual_saved_org.id == ORG_ID_2
    assert actual_saved_org.name == "PATCHED - Data For Good"
    assert actual_saved_org.description == "PATCHED - Data For Good Organization"


def test_orgganization_service_list_users():
    repository_mock: OrganizationRepository = mock.Mock(spec=OrganizationRepository)
    user_repository_mock: UserRepository = mock.Mock(spec=UserRepository)
    organization_service: OrganizationService = OrganizationService(
        user_repository=user_repository_mock,
        organization_repository=repository_mock,
        auth_context=FakeAuthContext(),
    )
    expected_org_users: List[OrganizationUser] = [ORG_USER]
    repository_mock.list_users.return_value = [ORG_USER]
    actual_user_list = organization_service.list_users(ORG_ID)
    assert actual_user_list == expected_org_users
