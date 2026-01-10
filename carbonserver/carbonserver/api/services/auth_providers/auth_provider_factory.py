"""
Authentication Provider Factory

This module provides a factory function to create the appropriate authentication
provider based on configuration settings.
"""

from typing import Optional

from carbonserver.api.services.auth_providers.auth_provider import AuthProvider
from carbonserver.api.services.auth_providers.no_auth_provider import NoAuthProvider
from carbonserver.api.services.auth_providers.oidc_auth_provider import OIDCAuthProvider
from carbonserver.config import settings


def create_auth_provider(provider_name: Optional[str] = None) -> AuthProvider:
    """
    Factory function to create an authentication provider based on configuration.

    Args:
        provider_name: Optional provider name override. If not provided,
                      uses the AUTH_PROVIDER setting from config.

    Returns:
        An instance of AuthProvider

    Raises:
        ValueError: If the provider name is not recognized

    Example:
        ```python
        # Using default from settings
        provider = create_auth_provider()

        # Override provider
        provider = create_auth_provider("none")
        ```
    """
    provider_type = provider_name or settings.auth_provider
    provider_type = provider_type.lower()

    if provider_type in ("oidc", "fief"):  # Support 'fief' for backward compatibility
        return OIDCAuthProvider(
            base_url=settings.oidc_issuer_url,
            client_id=settings.oidc_client_id,
            client_secret=settings.oidc_client_secret,
        )
    elif provider_type == "none":
        # No authentication - for development/internal use only
        return NoAuthProvider()
    else:
        raise ValueError(
            f"Unknown authentication provider: {provider_type}. "
            f"Supported providers: 'oidc', 'fief' (deprecated), 'none'"
        )


def get_auth_provider() -> AuthProvider:
    """
    Get the configured authentication provider instance.

    This is a convenience function that creates a provider using the
    settings from the environment.

    Returns:
        An instance of AuthProvider
    """
    return create_auth_provider()
