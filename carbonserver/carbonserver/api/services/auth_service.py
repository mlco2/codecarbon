import logging
from dataclasses import dataclass
from typing import Optional

import jwt
from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyCookie, HTTPBearer

from carbonserver.api.errors import AuthenticationError
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

        # The session cookie carries the OIDC provider's access token, so it is
        # treated exactly like a bearer token: both must be signature-verified.
        token = None
        if cookie_token is not None:
            token = cookie_token
        elif bearer_token is not None:
            token = bearer_token.credentials

        if token is None:
            self.auth_user = None
            self.db_user = None
            if self.error_if_not_found:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return self

        self.auth_user = await self._verify_token(token, auth_provider)

        try:
            self.db_user = user_service.get_user_by_id(self.auth_user["sub"])
        except Exception:
            self.db_user = None

        return self

    async def _verify_token(
        self, token: str, auth_provider: Optional[OIDCAuthProvider]
    ) -> dict:
        """
        Verify a session-cookie / bearer JWT and return its claims.

        The token is validated against the OIDC provider's JWKS (signature,
        expiry and standard claims). In the ``develop`` environment a locally
        minted token signed with the shared ``jwt_key`` (HS256) is accepted as a
        fallback so integration/black-box tests can authenticate without a live
        provider. Unsigned claims are never trusted.

        Raises:
            AuthenticationError: if the token cannot be verified.
        """
        if auth_provider is not None:
            try:
                return await auth_provider.get_user_info(token)
            except Exception:
                LOGGER.debug("JWKS validation of the token failed", exc_info=True)

        if settings.environment == "develop" and settings.jwt_key:
            try:
                return jwt.decode(token, settings.jwt_key, algorithms=["HS256"])
            except Exception:
                LOGGER.debug("develop jwt_key validation failed", exc_info=True)

        raise AuthenticationError()


OptionalUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=False)
MandatoryUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=True)
