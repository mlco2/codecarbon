"""
OIDC Authentication Provider Implementation

This module provides a generic OIDC authentication provider implementation using fastapi-oidc.
It can work with any OIDC-compliant provider (Fief, Keycloak, Auth0, etc.).
"""

import logging
from typing import Any, Dict, Optional, Tuple

from authlib.integrations.starlette_client import OAuth
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt
from fastapi import Response
from fief_client import FiefAsync

from carbonserver.config import settings

DEFAULT_SIGNATURE_CACHE_TTL = 3600  # seconds
OAUTH_SCOPES = ["openid", "email", "profile"]
LOGGER = logging.getLogger(__name__)

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
            access_token_info = await fief.validate_access_token(token)
            return access_token_info
        except Exception as e:
            LOGGER.error(f"Error validating access token: {e}")
            ...

        jwks_data = await self.client.fetch_jwk_set()
        keyset = JsonWebKey.import_key_set(jwks_data)
        claims = jose_jwt.decode(token, keyset)
        claims.validate()
        return dict(claims)

    async def validate_access_token(self, token: str) -> bool:
        await self._decode_token(token)
        return True

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        decoded_token = await self._decode_token(access_token)
        return decoded_token

    async def revoke_token(self, token: str) -> None:
        """Revoke an access token at the OIDC provider (RFC 7009).
        Best-effort — logs and swallows errors so logout always succeeds.
        """
        try:
            metadata = await self.client.load_server_metadata()
            revocation_endpoint = metadata.get("revocation_endpoint")
            if not revocation_endpoint:
                LOGGER.debug(
                    "OIDC provider does not expose a revocation_endpoint, "
                    "skipping token revocation"
                )
                return

            async with self.client._get_oauth_client(**metadata) as client:
                resp = await client.request(
                    "POST",
                    revocation_endpoint,
                    withhold_token=True,
                    data={
                        "token": token,
                        "token_type_hint": "access_token",
                    },
                )
                if resp.status_code == 200:
                    LOGGER.info("Access token revoked successfully")
                else:
                    LOGGER.warning(
                        "Token revocation returned status %s: %s",
                        resp.status_code,
                        resp.text,
                    )
        except Exception as e:
            LOGGER.warning("Token revocation failed (non-blocking): %s", e)

    @staticmethod
    def create_redirect_response(url: str) -> Response:
        """RedirectResponse doesn't work with clevercloud, so we return a HTML page with a script to redirect the user

        Ideally we should be able to do `response = RedirectResponse(url=url)` instead.
        """
        content = f"""<html>
            <head>
            <script>
            window.location.href = "{url}";
            </script>
            </head>
            </html>
            """
        response = Response(content=content)
        return response
