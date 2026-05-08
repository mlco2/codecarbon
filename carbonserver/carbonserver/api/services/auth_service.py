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
        auth_provider: Optional[OIDCAuthProvider] = Depends(
            Provide[ServerContainer.auth_provider]
        ),
    ):
        self.user_service = user_service
        if cookie_token is not None:
            self.auth_user = self._decode_cookie_token(cookie_token)
        elif bearer_token is not None:
            await self._validate_bearer_token(bearer_token, auth_provider)
            self.auth_user = self._decode_bearer_token(bearer_token)
        else:
            self.auth_user = None
            if self.error_if_not_found:
                raise HTTPException(
                    status_code=401,
                    detail="No token provided, please log in",
                )
        self.db_user = self._get_db_user(user_service)
        return self

    def _decode_cookie_token(self, cookie_token: str):
        try:
            return jwt.decode(
                cookie_token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
        except Exception:
            raise HTTPException(401, "Session expired, please log in")

    async def _validate_bearer_token(self, bearer_token, auth_provider):
        if settings.environment != "develop" and auth_provider is not None:
            try:
                await auth_provider.validate_access_token(bearer_token.credentials)
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token")

    def _decode_bearer_token(self, bearer_token) -> dict:
        try:
            auth_user = jwt.decode(
                bearer_token.credentials,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
        except Exception:
            LOGGER.warning("Failed to decode bearer token")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token, please log in again",
            )
        if settings.environment == "develop":
            try:
                auth_user = jwt.decode(
                    bearer_token.credentials,
                    settings.jwt_key,
                    algorithms=["HS256", "RS256"],
                )
            except Exception:
                pass
        return auth_user

    def _get_db_user(self, user_service) -> Optional[dict]:
        if self.auth_user is None:
            return None
        try:
            return user_service.get_user_by_id(self.auth_user["sub"])
        except Exception:

            return None


OptionalUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=False)
MandatoryUserWithAuthDependency = UserWithAuthDependency(error_if_not_found=True)
