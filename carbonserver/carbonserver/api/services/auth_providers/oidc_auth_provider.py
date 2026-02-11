"""
OIDC Authentication Provider Implementation

This module provides a generic OIDC authentication provider implementation using fastapi-oidc.
It can work with any OIDC-compliant provider (Fief, Keycloak, Auth0, etc.).
"""

from typing import Any, Dict, Optional, Tuple

from authlib.integrations.starlette_client import OAuth
from carbonserver.config import settings

DEFAULT_SIGNATURE_CACHE_TTL = 3600  # seconds
OAUTH_SCOPES = ["openid", "email", "profile"]


oauth = OAuth()
oauth.register(
    "client",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_well_known_url,
    client_kwargs={"scope": "openid profile email"},
)


class OIDCAuthProvider:
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        *,
        signature_cache_ttl: int = DEFAULT_SIGNATURE_CACHE_TTL,
        openid_configuration: Optional[Dict[str, Any]] = None,
    ):
        self.client = oauth._clients["client"]

    async def get_authorize_url(self, request, login_url):
        return await self.client.authorize_redirect(
            request, str(login_url), scope=" ".join(OAUTH_SCOPES)
        )

    def get_client_credentials(self) -> Tuple[str, str]:
        return (self.client.client_id, self.client.client_secret)
