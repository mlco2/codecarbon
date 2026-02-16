"""
OIDC Authentication Provider Implementation

This module provides a generic OIDC authentication provider implementation using fastapi-oidc.
It can work with any OIDC-compliant provider (Fief, Keycloak, Auth0, etc.).
"""

from typing import Any, Dict, Optional, Tuple

from authlib.integrations.starlette_client import OAuth
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt
from fief_client import FiefAsync

from carbonserver.config import settings

DEFAULT_SIGNATURE_CACHE_TTL = 3600  # seconds
OAUTH_SCOPES = ["openid", "email", "profile"]

fief = FiefAsync(
    settings.fief_url, settings.fief_client_id, settings.fief_client_secret
)

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

    async def _decode_token(self, token: str) -> Dict[str, Any]:
        try:
            print(f"Jwks_data: {token}")
            print(f"Base url: {fief.base_url}")
            print(f"Client id: {fief.client_id}")
            print(f"User info: {await fief.userinfo(token)}")
            access_token_info = await fief.validate_access_token(token)
            return access_token_info
        except Exception as e:
            print(f"Error validating access token: {e}")
            ...

        jwks_data = await self.client.fetch_jwk_set()
        print(f"Jwks_data: {jwks_data}")
        keyset = JsonWebKey.import_key_set(jwks_data)
        claims = jose_jwt.decode(token, keyset)
        claims.validate()
        print(f"Decoded claims: {claims}")
        print(f"Claims validate: {claims.validate()}")
        return dict(claims)

    async def validate_access_token(self, token: str) -> bool:
        await self._decode_token(token)
        return True
