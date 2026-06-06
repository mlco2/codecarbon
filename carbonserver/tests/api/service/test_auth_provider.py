"""
Unit tests for OIDC authentication provider.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from carbonserver.api.services.auth_providers import oidc_auth_provider
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

    @pytest.mark.asyncio
    async def test_decode_token_falls_back_to_jwks_when_fief_fails(self):
        """When fief.validate_access_token raises, _decode_token must fall back
        to the joserfc JWKS verification path and return a plain dict."""
        provider = OIDCAuthProvider(
            base_url="https://auth.example.com",
            client_id="test_client",
            client_secret="test_secret",
        )

        now = int(time.time())
        expected_claims = {
            "sub": "user-456",
            "iat": now - 5,
            "exp": now + 600,
            "email": "user@example.com",
        }

        jwks_payload = {"keys": [{"kty": "RSA", "kid": "k1"}]}
        provider.client = MagicMock()
        provider.client.fetch_jwk_set = AsyncMock(return_value=jwks_payload)

        decoded_token = MagicMock()
        decoded_token.claims = expected_claims

        with (
            patch.object(
                oidc_auth_provider.fief,
                "validate_access_token",
                new=AsyncMock(side_effect=Exception("fief unavailable")),
            ),
            patch.object(
                oidc_auth_provider.KeySet,
                "import_key_set",
                return_value="keyset",
            ) as mock_import,
            patch.object(
                oidc_auth_provider.jose_jwt,
                "decode",
                return_value=decoded_token,
            ) as mock_decode,
        ):
            result = await provider._decode_token("opaque-token")

        assert result == expected_claims
        assert isinstance(result, dict)
        mock_import.assert_called_once_with(jwks_payload)
        mock_decode.assert_called_once_with("opaque-token", "keyset")
