"""
OIDC Authentication helpers for the CodeCarbon CLI.

Handles the full token lifecycle: browser-based login (Authorization Code +
PKCE), credential storage, JWKS validation, and transparent refresh.
"""

import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from authlib.common.security import generate_token
from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt
from authlib.oauth2.rfc7636 import create_s256_code_challenge

AUTH_CLIENT_ID = os.environ.get(
    "AUTH_CLIENT_ID",
    "codecarbon-cli",
)
AUTH_SERVER_WELL_KNOWN = os.environ.get(
    "AUTH_SERVER_WELL_KNOWN",
    "https://authentication.codecarbon.io/realms/codecarbon/.well-known/openid-configuration",
)

_REDIRECT_PORT = 8090
_REDIRECT_URI = f"http://localhost:{_REDIRECT_PORT}/callback"
_CREDENTIALS_FILE = Path("./credentials.json")


# ── OAuth callback server ───────────────────────────────────────────


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth2 authorization callback."""

    callback_url = None
    error = None

    def do_GET(self):
        _CallbackHandler.callback_url = f"http://localhost:{_REDIRECT_PORT}{self.path}"
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "error" in params:
            _CallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            msg = params.get("error_description", [params["error"][0]])[0]
            self.wfile.write(
                f"<html><body><h1>Login failed</h1><p>{msg}</p></body></html>".encode()
            )
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Login successful!</h1>"
                b"<p>You can close this window.</p></body></html>"
            )

    def log_message(self, format, *args):
        pass


# ── OIDC discovery ──────────────────────────────────────────────────


def _discover_endpoints():
    """Fetch OpenID Connect discovery document."""
    resp = requests.get(AUTH_SERVER_WELL_KNOWN)
    resp.raise_for_status()
    return resp.json()


# ── Credential storage ──────────────────────────────────────────────


def _save_credentials(tokens):
    """Save OAuth tokens to the local credentials file."""
    with open(_CREDENTIALS_FILE, "w") as f:
        json.dump(tokens, f)


def _load_credentials():
    """Load OAuth tokens from the local credentials file."""
    with open(_CREDENTIALS_FILE, "r") as f:
        return json.load(f)


# ── Token validation & refresh ──────────────────────────────────────


def _validate_access_token(access_token: str) -> bool:
    """Validate access token against the current OIDC provider's JWKS.

    Returns False when the signature or expiry check fails (wrong provider,
    expired, tampered).  Returns True on network errors so the caller can
    fall through to the API and let the server decide.
    """
    try:
        discovery = _discover_endpoints()
        jwks_resp = requests.get(discovery["jwks_uri"])
        jwks_resp.raise_for_status()
        keyset = JsonWebKey.import_key_set(jwks_resp.json())
        claims = jose_jwt.decode(access_token, keyset)
        claims.validate()
        return True
    except requests.RequestException:
        return True  # Can't reach auth server — let the API handle it
    except Exception:
        return False


def _refresh_tokens(refresh_token: str) -> dict:
    """Exchange a refresh token for a new token set via the OIDC token endpoint."""
    discovery = _discover_endpoints()
    resp = requests.post(
        discovery["token_endpoint"],
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": AUTH_CLIENT_ID,
        },
    )
    resp.raise_for_status()
    return resp.json()


# ── Public API ──────────────────────────────────────────────────────


def authorize():
    """Run the OAuth2 Authorization Code flow with PKCE."""
    discovery = _discover_endpoints()

    session = OAuth2Session(
        client_id=AUTH_CLIENT_ID,
        redirect_uri=_REDIRECT_URI,
        scope="openid offline_access",
        token_endpoint_auth_method="none",
    )

    code_verifier = generate_token(48)
    code_challenge = create_s256_code_challenge(code_verifier)

    uri, state = session.create_authorization_url(
        discovery["authorization_endpoint"],
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )

    _CallbackHandler.callback_url = None
    _CallbackHandler.error = None

    server = HTTPServer(("localhost", _REDIRECT_PORT), _CallbackHandler)

    print("Opening browser for authentication...")
    webbrowser.open(uri)

    server.handle_request()
    server.server_close()

    if _CallbackHandler.error:
        raise ValueError(f"Authorization failed: {_CallbackHandler.error}")

    if not _CallbackHandler.callback_url:
        raise ValueError("Authorization failed: no callback received")

    token = session.fetch_token(
        discovery["token_endpoint"],
        authorization_response=_CallbackHandler.callback_url,
        code_verifier=code_verifier,
    )

    _save_credentials(token)
    return token


def get_access_token() -> str:
    """Return a valid access token, refreshing or failing with a clear message."""
    try:
        creds = _load_credentials()
    except Exception as e:
        raise ValueError(
            "Not able to retrieve the access token, "
            f"please run `codecarbon login` first! (error: {e})"
        )

    access_token = creds.get("access_token")
    if not access_token:
        raise ValueError("No access token found. Please run `codecarbon login` first.")

    # Fast path: token is still valid for the current OIDC provider
    if _validate_access_token(access_token):
        return access_token

    # Token is expired or was issued by a different provider — try refresh
    refresh_token = creds.get("refresh_token")
    if refresh_token:
        try:
            new_tokens = _refresh_tokens(refresh_token)
            _save_credentials(new_tokens)
            return new_tokens["access_token"]
        except Exception:
            pass

    # Refresh failed — credentials are stale (e.g. auth provider migrated)
    _CREDENTIALS_FILE.unlink(missing_ok=True)
    raise ValueError(
        "Your session has expired or the authentication provider has changed. "
        "Please run `codecarbon login` again."
    )


def get_id_token() -> str:
    """Return the stored OIDC id_token."""
    creds = _load_credentials()
    return creds["id_token"]
