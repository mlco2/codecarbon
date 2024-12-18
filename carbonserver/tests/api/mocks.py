from carbonserver.api.schemas import User

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ORGANIZATION_ID = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"
ORGANIZATION_ID_2 = "c13e851f-5c2f-403d-98d0-51fe15df3bc4"
DUMMY_USER = User(
    id=USER_ID_1,
    name="Gontran Bonheur",
    email="gontran.bonheur@gmail.com",
    organizations=[ORGANIZATION_ID, ORGANIZATION_ID_2],
    is_active=True,
)


class FakeUserWithAuthDependency:
    auth_user = {"sub": USER_ID_1}
    db_user = DUMMY_USER


class FakeAuthContext:
    @staticmethod
    def isOperationAuthorizedOnOrg(*args, **kwargs):
        return True

    @staticmethod
    def isOperationAuthorizedOnProject(*args, **kwargs):
        return True

    @staticmethod
    def can_read_organization(*args, **kwargs):
        return True

    @staticmethod
    def can_write_organization(*args, **kwargs):
        return True
