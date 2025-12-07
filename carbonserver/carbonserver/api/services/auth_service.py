from dataclasses import dataclass
from typing import Optional

import jwt
from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyCookie, HTTPBearer, OAuth2AuthorizationCodeBearer

from carbonserver.api.services.auth_providers.auth_provider import AuthProvider
from carbonserver.api.services.user_service import UserService
from carbonserver.config import settings
from carbonserver.container import ServerContainer

OAUTH_SCOPES = ["openid", "email", "profile"]


@dataclass
class FullUser:
    db_user: dict
    auth_user: dict


SESSION_COOKIE_NAME = "user_session"


def get_oauth_scheme(auth_provider: AuthProvider) -> OAuth2AuthorizationCodeBearer:
    """
    Get the OAuth2 scheme for the configured auth provider.

    Args:
        auth_provider: The authentication provider instance

    Returns:
        OAuth2AuthorizationCodeBearer configured for the provider
    """
    return OAuth2AuthorizationCodeBearer(
        auth_provider.get_authorize_endpoint(),
        auth_provider.get_token_endpoint(),
        scopes={x: x for x in OAUTH_SCOPES},
        auto_error=False,
    )


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
        auth_provider: AuthProvider = Depends(Provide[ServerContainer.auth_provider]),
    ):
        self.user_service = user_service
        if cookie_token is not None:
            self.auth_user = jwt.decode(
                cookie_token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
        elif bearer_token is not None:
            if settings.environment != "develop":
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
