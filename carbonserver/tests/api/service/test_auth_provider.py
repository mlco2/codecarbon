"""
Unit tests for OIDC authentication provider.
"""

from carbonserver.api.services.auth_providers.oidc_auth_provider import OIDCAuthProvider


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
        assert hasattr(provider, "get_auth_url")
        assert hasattr(provider, "handle_auth_callback")
        assert hasattr(provider, "validate_access_token")
        assert hasattr(provider, "get_user_info")
        assert hasattr(provider, "get_token_endpoint")
        assert hasattr(provider, "get_authorize_endpoint")
        assert hasattr(provider, "get_client_credentials")

        # Test endpoint methods
        assert provider.get_token_endpoint() == "https://auth.example.com/api/token"
        assert provider.get_authorize_endpoint() == "https://auth.example.com/authorize"
        assert provider.get_client_credentials() == ("test_client", "test_secret")

    def test_oidc_provider_base_url_normalization(self):
        """Test that base URL is normalized correctly."""
        provider = OIDCAuthProvider(
            base_url="https://auth.example.com/",  # trailing slash
            client_id="test_client",
            client_secret="test_secret",
        )

        assert provider.base_url == "https://auth.example.com"
