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

        assert hasattr(provider, "get_authorize_url")
        assert hasattr(provider, "get_user_info")
