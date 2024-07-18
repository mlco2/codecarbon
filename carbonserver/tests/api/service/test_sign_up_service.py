from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrgSqlRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectSqlRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserSqlRepository,
)
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    Project,
    ProjectCreate,
    User,
    UserCreate,
)
from carbonserver.api.services.signup_service import SignUpService

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"
INVALID_API_KEY = "8INn3JsdhCGzLAuOUC6rAw"

ORG_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("f688133d-2cb9-41f0-9362-a4c05ceb0dd8")

ORG_1 = Organization(
    id=ORG_ID,
    name="DFG",
    api_key=API_KEY,
    description="Data For Good Organization",
)

ORG_2 = Organization(
    id=ORG_ID_2,
    name="ORG2",
    api_key=API_KEY,
    description="Data For Good Organization 2",
)


USER_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

USER_1 = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    api_key=API_KEY,
    organizations=[],
    is_active=True,
)

USER_IN_DEFAULT_ORG = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    api_key=API_KEY,
    organizations=[ORG_ID],
    is_active=True,
)


PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

PROJECT_1 = {
    "id": PROJECT_ID,
    "name": "Gontran Bonheur",
    "description": "Default project",
    "organization_id": ORG_ID,
    "experiments": [],
}
DEFAULT_ORG = OrganizationCreate(
    **{
        "id": ORG_ID,
        "api_key": API_KEY,
        "name": "Gontran Bonheur",
        "description": "Default organization",
    }
)
###


def test_sign_up_service_creates_user_with_default_project_and_organisation():
    org_repository_mock: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    user_repository_mock: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    project_repository_mock: UserSqlRepository = mock.Mock(spec=ProjectSqlRepository)
    org_repository_mock.add_organization.return_value = ORG_1
    user_repository_mock.create_user.return_value = USER_1
    user_repository_mock.subscribe_user_to_org.return_value = USER_IN_DEFAULT_ORG
    expected_project = PROJECT_1
    project_repository_mock.add_project.return_value = Project(**expected_project)

    signup_service: SignUpService = SignUpService(
        user_repository_mock, org_repository_mock, project_repository_mock
    )
    user_to_create = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )
    signup_service.sign_up(user_to_create)

    # Check that the mocks have been called
    user_repository_mock.create_user.assert_called_once()
    user_repository_mock.subscribe_user_to_org.assert_called_once()
    project_repository_mock.add_project.assert_called_once()
    org_repository_mock.add_organization.assert_called_once()
    # Check that the mocks have been called with the correct arguments
    user_repository_mock.create_user.assert_called_with(user_to_create)
    user_repository_mock.subscribe_user_to_org.assert_called_with(USER_1, ORG_ID)
    project_repository_mock.add_project.assert_called_with(ProjectCreate(**PROJECT_1))
    org_repository_mock.add_organization.assert_called_with(DEFAULT_ORG)


def test_add_user_to_org_adds_user_if_api_key_is_correct():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    project_repository_mock: UserSqlRepository = mock.Mock(spec=ProjectSqlRepository)

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, project_repository_mock
    )

    signup_service.subscribe_user_to_org(USER_1, ORG_ID_2, API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID_2, API_KEY)
    user_mock_repository.subscribe_user_to_org.assert_called_with(USER_1, ORG_ID_2)


def test_add_user_to_org_rejects_user_if_api_key_is_incorrect():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    project_repository_mock: UserSqlRepository = mock.Mock(spec=ProjectSqlRepository)
    org_mock_repository.is_api_key_valid.return_value = False
    user_mock_repository.subscribe_user_to_org.return_value = USER_IN_DEFAULT_ORG

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, project_repository_mock
    )

    signup_service.subscribe_user_to_org(USER_1, ORG_ID_2, INVALID_API_KEY)
    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID_2, INVALID_API_KEY)
    assert not user_mock_repository.subscribe_user_to_org.called
