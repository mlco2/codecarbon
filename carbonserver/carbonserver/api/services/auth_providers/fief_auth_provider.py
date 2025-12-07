"""
Fief Authentication Provider Implementation

This module provides a concrete implementation of AuthProvider using Fief.
"""

from typing import Any, Dict, List, Optional, Tuple

from fief_client import FiefAsync

from carbonserver.api.services.auth_providers.auth_provider import AuthProvider


class FiefAuthProvider(AuthProvider):
    """
    Fief-based authentication provider implementation.

    This class wraps the Fief client to provide authentication services
    through the AuthProvider interface.
    """

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        """
        Initialize the Fief authentication provider.

        Args:
            base_url: The Fief server base URL
            client_id: The OAuth2 client ID
            client_secret: The OAuth2 client secret
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = FiefAsync(base_url, client_id, client_secret)

    async def get_auth_url(
        self, redirect_uri: str, scope: List[str], state: Optional[str] = None
    ) -> str:
        """
        Generate the authorization URL for the OAuth2 flow using Fief.

        Args:
            redirect_uri: The URI to redirect to after authentication
            scope: List of OAuth2 scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            The authorization URL to redirect the user to
        """
        return await self._client.auth_url(redirect_uri, scope=scope, state=state)

    async def handle_auth_callback(
        self, code: str, redirect_uri: str
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Handle the OAuth2 callback and exchange the code for tokens using Fief.

        Args:
            code: The authorization code from the OAuth2 provider
            redirect_uri: The redirect URI used in the initial auth request

        Returns:
            A tuple of (tokens, user_info) where:
            - tokens: Dict containing access_token, refresh_token, expires_in, etc.
            - user_info: Optional dict containing user information
        """
        tokens, user_info = await self._client.auth_callback(code, redirect_uri)
        # Convert Fief objects to dicts
        tokens_dict = dict(tokens)
        user_info_dict = dict(user_info) if user_info else None
        return (tokens_dict, user_info_dict)

    async def validate_access_token(self, token: str) -> bool:
        """
        Validate an access token with Fief.

        Args:
            token: The access token to validate

        Returns:
            True if the token is valid

        Raises:
            Exception if validation fails
        """
        await self._client.validate_access_token(token)
        return True

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Fief.

        Args:
            access_token: The access token for the user

        Returns:
            Dict containing user information (sub, email, name, etc.)
        """
        user_info = await self._client.userinfo(access_token)
        return dict(user_info)

    def get_token_endpoint(self) -> str:
        """
        Get the token endpoint URL for Fief.

        Returns:
            The token endpoint URL
        """
        return f"{self.base_url}/api/token"

    def get_authorize_endpoint(self) -> str:
        """
        Get the authorization endpoint URL for Fief.

        Returns:
            The authorization endpoint URL
        """
        return f"{self.base_url}/authorize"

    def get_client_credentials(self) -> Tuple[str, str]:
        """
        Get the client ID and client secret.

        Returns:
            A tuple of (client_id, client_secret)
        """
        return (self.client_id, self.client_secret)
