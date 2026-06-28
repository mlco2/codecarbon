import logging
from dataclasses import dataclass
from typing import Optional

import jwt
from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyCookie, HTTPBearer

from carbonserver.api.services.auth_providers.oidc_auth_provider import (
    OIDCAuthProvider,
)
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService
from carbonserver.config import settings
from carbonserver.container import ServerContainer

OAUTH_SCOPES = ["openid", "email", "profile"]
LOGGER = logging.getLogger(__name__)


@dataclass
class FullUser:
    db_user: dict
    auth_user: dict


SESSION_COOKIE_NAME = "user_session"
LOCAL_DEV_AUTH_USER = {
    "sub": "d1b9d5e0-58e8-45f0-9ef5-4549b3d6f3f0",
    "email": "local.user@example.com",
    "fields": {"name": "Local user"},
}


web_scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)


class UserWithAuthDependency:
    """
    Used to reconciliate oauth and db sides for a user
    Auth token can be passed as bearer token or cookie
    """

    def __init__(self, error_if_not_found=False):
        """
        :param error_if_not_found: If True, will raise an exception if user is not authenticated
        """
        self.error_if_not_found = error_if_not_found

    async def __call__(
        self,
        cookie_token: Optional[str] = Depends(web_scheme),
        bearer_token: Optional[str] = Depends(HTTPBearer(auto_error=False)),
        user_service: Optional[UserService] = Depends(
            Provide[ServerContainer.user_service]
        ),
        sign_up_service: Optional[SignUpService] = Depends(
            Provide[ServerContainer.sign_up_service]
        ),
        auth_provider: Optional[OIDCAuthProvider] = Depends(
            Provide[ServerContainer.auth_provider]
        ),
    ):
        self.user_service = user_service
        if settings.auth_provider.lower() == "none":
            self.auth_user = LOCAL_DEV_AUTH_USER
            sign_up_service.check_jwt_user(self.auth_user, create=True)
            self.db_user = user_service.get_user_by_id(self.auth_user["sub"])
            return self

        if cookie_token is not None:
            self.auth_user = jwt.decode(
                cookie_token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
        elif bearer_token is not None:
            if settings.environment != "develop" and auth_provider is not None:
                LOGGER.debug(
                    f"Validating token with auth provider. Token: {bearer_token}"
                )
                try:
                    await auth_provider.validate_access_token(bearer_token.credentials)
                except Exception:
                    raise HTTPException(status_code=401, detail="Invalid token")
            # cli user using auth provider token
            self.auth_user = jwt.decode(
                bearer_token.credentials,
                options={"verify_signature": False},
                algorithms=[
                    "HS256",
                    "RS256",
                ],
            )
            if settings.environment == "develop":
                try:
                    # test user
                    self.auth_user = jwt.decode(
                        bearer_token.credentials,
                        settings.jwt_key,
                        algorithms=[
                            "HS256",
                            "RS256",
                        ],
                    )
                except Exception:
                    ...
        else:
            self.auth_user = None
            if self.error_if_not_found:
                raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            self.db_user = user_service.get_user_by_id(self.auth_user["sub"])
        except Exception:
            self.db_user = None

        return self


OptionalUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=False)
MandatoryUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=True)
