"""
Unit tests for OIDC authentication provider.
"""

from carbonserver.api.services.auth_providers.oidc_auth_provider import OIDCAuthProvider
from carbonserver.config import settings


class TestOIDCAuthProvider:
    """Test OIDC authentication provider implementation."""

    def test_oidc_provider_initialization(self):
        """Test that OIDCAuthProvider initializes correctly."""
        provider = OIDCAuthProvider(
            base_url="https://auth.example.com",
            client_id="test_client",
            client_secret="test_secret",
        )

        # Check all required methods exist
        assert hasattr(provider, "get_authorize_url")
        assert hasattr(provider, "get_client_credentials")

        # Test endpoint methods
        assert provider.get_client_credentials() == (
            settings.oidc_client_id,
            settings.oidc_client_secret,
        )
