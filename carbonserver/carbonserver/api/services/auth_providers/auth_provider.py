"""
Authentication Provider Interface

This module defines an abstract interface for authentication providers.
To implement a custom authentication provider, create a class that inherits
from AuthProvider and implements all the required methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class AuthProvider(ABC):
    """
    Abstract base class for authentication providers.

    This interface allows CodeCarbon to support multiple authentication providers
    (Fief, Auth0, Keycloak, custom OAuth2, etc.) by implementing this interface.
    """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def validate_access_token(self, token: str) -> bool:
        """
        Validate an access token.

        Args:
            token: The access token to validate

        Returns:
            True if the token is valid, False otherwise

        Raises:
            Exception if validation fails
        """

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from the authentication provider.

        Args:
            access_token: The access token for the user

        Returns:
            Dict containing user information (sub, email, name, etc.)
        """

    @abstractmethod
    def get_token_endpoint(self) -> str:
        """
        Get the token endpoint URL for the provider.

        Returns:
            The token endpoint URL
        """

    @abstractmethod
    def get_authorize_endpoint(self) -> str:
        """
        Get the authorization endpoint URL for the provider.

        Returns:
            The authorization endpoint URL
        """

    @abstractmethod
    def get_client_credentials(self) -> Tuple[str, str]:
        """
        Get the client ID and client secret.

        Returns:
            A tuple of (client_id, client_secret)
        """
