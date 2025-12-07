"""
Unit tests for authentication provider interface and implementations.
"""

import pytest

from carbonserver.api.services.auth_providers.fief_auth_provider import FiefAuthProvider


class TestAuthProviderInterface:
    """Test that providers implement the interface correctly."""

    def test_no_auth_provider_interface(self):
        """Test that NoAuthProvider implements all required methods."""
        from carbonserver.api.services.auth_providers.no_auth_provider import (
            NoAuthProvider,
        )

        provider = NoAuthProvider()

        # Check all required methods exist
        assert hasattr(provider, "get_auth_url")
        assert hasattr(provider, "handle_auth_callback")
        assert hasattr(provider, "validate_access_token")
        assert hasattr(provider, "get_user_info")
        assert hasattr(provider, "get_token_endpoint")
        assert hasattr(provider, "get_authorize_endpoint")
        assert hasattr(provider, "get_client_credentials")

        # Test synchronous endpoint methods
        assert provider.get_token_endpoint() == "http://localhost/token"
        assert provider.get_authorize_endpoint() == "http://localhost/authorize"
        assert provider.get_client_credentials() == ("no-auth", "no-auth")

    def test_fief_provider_interface(self):
        """Test that FiefAuthProvider implements all required methods."""
        provider = FiefAuthProvider(
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


class TestAuthProviderFactory:
    """Test the auth provider factory."""

    def test_factory_creates_fief_provider(self):
        """Test that factory creates Fief provider when configured."""
        from carbonserver.api.services.auth_providers.auth_provider_factory import (
            create_auth_provider,
        )

        provider = create_auth_provider("fief")
        assert isinstance(provider, FiefAuthProvider)

    def test_factory_creates_no_auth_provider(self):
        """Test that factory creates no-auth provider when configured."""
        from carbonserver.api.services.auth_providers.auth_provider_factory import (
            create_auth_provider,
        )
        from carbonserver.api.services.auth_providers.no_auth_provider import (
            NoAuthProvider,
        )

        provider = create_auth_provider("none")
        assert isinstance(provider, NoAuthProvider)

    def test_factory_raises_on_unknown_provider(self):
        """Test that factory raises error for unknown provider."""
        from carbonserver.api.services.auth_providers.auth_provider_factory import (
            create_auth_provider,
        )

        with pytest.raises(ValueError, match="Unknown authentication provider"):
            create_auth_provider("unknown_provider")
