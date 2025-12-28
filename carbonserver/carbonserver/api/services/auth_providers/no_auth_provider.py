"""
No Authentication Provider

This provider allows running CodeCarbon without authentication requirements.
Useful for local development, internal networks, or testing environments.

WARNING: Do not use in production environments exposed to the internet!
"""

from typing import Any, Dict, List, Optional, Tuple

from carbonserver.api.services.auth_providers.auth_provider import AuthProvider


class NoAuthProvider(AuthProvider):
    """
    No-authentication provider for development and internal use.

    This provider bypasses authentication checks and always succeeds.
    It's useful for:
    - Local development without setting up OAuth
    - Internal networks with other security measures
    - Testing and CI/CD pipelines

    WARNING: Never use this in production environments exposed to the internet!
    """

    def __init__(self):
        """Initialize the no-auth provider."""
        self.base_url = "http://localhost"
        self.client_id = "no-auth"
        self.client_secret = "no-auth"

    async def get_auth_url(
        self, redirect_uri: str, scope: List[str], state: Optional[str] = None
    ) -> str:
        """
        Return a dummy auth URL (not used in no-auth mode).

        Args:
            redirect_uri: The URI to redirect to after authentication
            scope: List of OAuth2 scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            The redirect URI (authentication is bypassed)
        """
        return redirect_uri

    async def handle_auth_callback(
        self, code: str, redirect_uri: str
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Return dummy tokens and user info (authentication bypassed).

        Args:
            code: The authorization code from the OAuth2 provider
            redirect_uri: The redirect URI used in the initial auth request

        Returns:
            A tuple of (tokens, user_info) with default values
        """
        tokens = {
            "access_token": "no-auth-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        user_info = {
            "sub": "no-auth-user",
            "email": "noauth@localhost",
            "name": "No Auth User",
        }
        return (tokens, user_info)

    async def validate_access_token(self, token: str) -> bool:
        """
        Always return True (no validation in no-auth mode).

        Args:
            token: The access token to validate

        Returns:
            Always True
        """
        return True

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Return default user info (no actual authentication).

        Args:
            access_token: The access token for the user

        Returns:
            Dict containing default user information
        """
        return {
            "sub": "no-auth-user",
            "email": "noauth@localhost",
            "name": "No Auth User",
        }

    def get_token_endpoint(self) -> str:
        """
        Get a dummy token endpoint URL.

        Returns:
            The token endpoint URL (not used)
        """
        return f"{self.base_url}/token"

    def get_authorize_endpoint(self) -> str:
        """
        Get a dummy authorization endpoint URL.

        Returns:
            The authorization endpoint URL (not used)
        """
        return f"{self.base_url}/authorize"

    def get_client_credentials(self) -> Tuple[str, str]:
        """
        Get dummy client credentials.

        Returns:
            A tuple of (client_id, client_secret)
        """
        return (self.client_id, self.client_secret)
