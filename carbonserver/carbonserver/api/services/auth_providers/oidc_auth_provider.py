"""
OIDC Authentication Provider Implementation

This module provides a generic OIDC authentication provider implementation using fastapi-oidc.
It can work with any OIDC-compliant provider (Fief, Keycloak, Auth0, etc.).
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from fastapi_oidc import discovery
from jose import jwt

DEFAULT_SIGNATURE_CACHE_TTL = 3600  # seconds


class OIDCAuthProvider:
    """
    Generic OIDC authentication provider implementation.

    This class uses OIDC discovery and validation (via fastapi-oidc) to interact with
    any OIDC-compliant authentication server (such as Fief, Keycloak, Auth0, etc.).
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        *,
        signature_cache_ttl: int = DEFAULT_SIGNATURE_CACHE_TTL,
        openid_configuration: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the OIDC authentication provider.

        Args:
            base_url: The OIDC issuer URL (base URL of the authentication server)
            client_id: The OAuth2 client ID
            client_secret: The OAuth2 client secret
            signature_cache_ttl: Seconds to cache the OIDC discovery/JWKS responses
            openid_configuration: Optional pre-loaded OIDC configuration (used mainly for testing)
        """
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._discovery = discovery.configure(cache_ttl=signature_cache_ttl)
        self._openid_configuration = openid_configuration

    async def _get_openid_configuration(self) -> Dict[str, Any]:
        if self._openid_configuration is None:
            self._openid_configuration = await asyncio.to_thread(
                self._discovery.auth_server, base_url=self.base_url
            )
        return self._openid_configuration

    async def _get_jwks(self) -> Dict[str, Any]:
        oidc_config = await self._get_openid_configuration()
        return await asyncio.to_thread(self._discovery.public_keys, oidc_config)

    async def _get_algorithms(self) -> List[str]:
        oidc_config = await self._get_openid_configuration()
        return await asyncio.to_thread(self._discovery.signing_algos, oidc_config)

    async def _decode_token(self, token: str) -> Dict[str, Any]:
        oidc_config = await self._get_openid_configuration()
        jwks = await self._get_jwks()
        algorithms = await self._get_algorithms()
        return jwt.decode(
            token,
            jwks,
            algorithms=algorithms,
            issuer=oidc_config.get("issuer", self.base_url),
            options={"verify_aud": False, "verify_at_hash": False},
        )

    async def get_auth_url(
        self, redirect_uri: str, scope: List[str], state: Optional[str] = None
    ) -> str:
        """
        Generate the authorization URL for the OAuth2 flow.

        Args:
            redirect_uri: The URI to redirect to after authentication
            scope: List of OAuth2 scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            The authorization URL to redirect the user to
        """
        oidc_config = await self._get_openid_configuration()
        authorize_endpoint = oidc_config.get(
            "authorization_endpoint", f"{self.base_url}/authorize"
        )
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scope),
        }
        if state is not None:
            params["state"] = state

        return f"{authorize_endpoint}?{urlencode(params)}"

    async def handle_auth_callback(
        self, code: str, redirect_uri: str
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Handle the OAuth2 callback and exchange the code for tokens.

        Args:
            code: The authorization code from the OAuth2 provider
            redirect_uri: The redirect URI used in the initial auth request

        Returns:
            A tuple of (tokens, user_info) where:
            - tokens: Dict containing access_token, refresh_token, expires_in, etc.
            - user_info: Optional dict containing user information
        """
        oidc_config = await self._get_openid_configuration()
        token_endpoint = oidc_config.get("token_endpoint", f"{self.base_url}/api/token")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            tokens: Dict[str, Any] = response.json()

        user_info: Optional[Dict[str, Any]] = None
        if "id_token" in tokens:
            user_info = await self._decode_token(tokens["id_token"])
        elif "access_token" in tokens:
            try:
                user_info = await self.get_user_info(tokens["access_token"])
            except Exception:
                # If userinfo fails we still return tokens
                user_info = None

        return (tokens, user_info)

    async def validate_access_token(self, token: str) -> bool:
        """
        Validate an access token.

        Args:
            token: The access token to validate

        Returns:
            True if the token is valid

        Raises:
            Exception if validation fails
        """
        await self._decode_token(token)
        return True

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from the OIDC provider.

        Args:
            access_token: The access token for the user

        Returns:
            Dict containing user information (sub, email, name, etc.)
        """
        oidc_config = await self._get_openid_configuration()
        userinfo_endpoint = oidc_config.get(
            "userinfo_endpoint", f"{self.base_url}/api/userinfo"
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)
            response.raise_for_status()
            return response.json()

    def get_token_endpoint(self) -> str:
        """
        Get the token endpoint URL.

        Returns:
            The token endpoint URL
        """
        if (
            self._openid_configuration
            and "token_endpoint" in self._openid_configuration
        ):
            return self._openid_configuration["token_endpoint"]
        return f"{self.base_url}/api/token"

    def get_authorize_endpoint(self) -> str:
        """
        Get the authorization endpoint URL.

        Returns:
            The authorization endpoint URL
        """
        if (
            self._openid_configuration
            and "authorization_endpoint" in self._openid_configuration
        ):
            return self._openid_configuration["authorization_endpoint"]
        return f"{self.base_url}/authorize"

    def get_client_credentials(self) -> Tuple[str, str]:
        """
        Get the client ID and client secret.

        Returns:
            A tuple of (client_id, client_secret)
        """
        return (self.client_id, self.client_secret)
