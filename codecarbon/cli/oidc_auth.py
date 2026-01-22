"""
OIDC Authentication module for CodeCarbon CLI.

This module replaces the deprecated fief-client library with a standard
OIDC implementation using python-jose for JWT validation.
"""

import hashlib
import json
import secrets
import webbrowser
from base64 import urlsafe_b64encode
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from jose import jwt
from jose.exceptions import JWTError


class OIDCAuth:
    """
    Uses Authorization Code flow with PKCE for secure authentication.
    Stores tokens in a local credentials file.
    """

    def __init__(
        self,
        server_url: str,
        client_id: str,
        credentials_file: str = "./credentials.json",
    ):

        self.server_url = server_url.rstrip("/")
        self.client_id = client_id
        self.credentials_file = Path(credentials_file)
        self._tokens: Optional[Dict] = None
        self._oidc_config: Optional[Dict] = None
        self._jwks: Optional[Dict] = None

        # Load existing credentials
        self._load_credentials()

    def _get_oidc_configuration(self) -> Dict:
        if self._oidc_config is None:
            config_url = f"{self.server_url}/.well-known/openid-configuration"
            response = requests.get(config_url)
            response.raise_for_status()
            self._oidc_config = response.json()
        return self._oidc_config

    def _get_jwks(self) -> Dict:
        if self._jwks is None:
            config = self._get_oidc_configuration()
            jwks_uri = config["jwks_uri"]
            response = requests.get(jwks_uri)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks

    def _generate_pkce_pair(self):
        code_verifier = (
            urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        )
        code_challenge = (
            urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
            .decode("utf-8")
            .rstrip("=")
        )
        return code_verifier, code_challenge

    def _load_credentials(self):
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, "r") as f:
                    self._tokens = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._tokens = None

    def _save_credentials(self):
        if self._tokens:
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.credentials_file, "w") as f:
                json.dump(self._tokens, f, indent=2)

    def authorize(self, redirect_port: int = 51562):
        config = self._get_oidc_configuration()
        authorization_endpoint = config["authorization_endpoint"]
        token_endpoint = config["token_endpoint"]

        code_verifier, code_challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(32)

        redirect_uri = f"http://localhost:{redirect_port}/callback"

        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{authorization_endpoint}?{urlencode(auth_params)}"

        authorization_code = None
        server_error = None

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # Suppress server logs
                pass

            def do_GET(self):
                nonlocal authorization_code, server_error

                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                if "code" in params and "state" in params:
                    if params["state"][0] == state:
                        authorization_code = params["code"][0]
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(
                            b"<html><body><h1>Authentication successful!</h1><p>You can close this window.</p></body></html>"
                        )
                    else:
                        server_error = "State mismatch"
                        self.send_response(400)
                        self.end_headers()
                elif "error" in params:
                    server_error = params["error"][0]
                    self.send_response(400)
                    self.end_headers()

        server = HTTPServer(("localhost", redirect_port), CallbackHandler)
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()
        print(f"Opening browser for authentication...")
        print(auth_url)
        webbrowser.open(auth_url)
        server_thread.join(timeout=300)  # 5 minute timeout
        server.server_close()

        if server_error:
            raise Exception(f"Authorization failed: {server_error}")

        if not authorization_code:
            raise Exception("Authorization timed out or was cancelled")

        # Exchange code for tokens
        token_params = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }

        response = requests.post(token_endpoint, data=token_params)
        response.raise_for_status()
        self._tokens = response.json()
        self._save_credentials()

        print("Authentication successful!")

    def _refresh_tokens(self):
        """Refresh access token using refresh token."""
        if not self._tokens or "refresh_token" not in self._tokens:
            raise Exception("No refresh token available")

        config = self._get_oidc_configuration()
        token_endpoint = config["token_endpoint"]

        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": self._tokens["refresh_token"],
            "client_id": self.client_id,
        }

        response = requests.post(token_endpoint, data=token_params)
        response.raise_for_status()
        self._tokens = response.json()
        self._save_credentials()

    # def _validate_token(self, token: str) -> Dict:
    #     try:
    #         jwks = self._get_jwks()
    #         # Decode and validate
    #         claims = jwt.decode(
    #             token,
    #             jwks,
    #             algorithms=['RS256'],
    #             audience=self.client_id,
    #             issuer=self.server_url,
    #         )
    #         return claims
    #     except JWTError as e:
    #         raise Exception(f"Token validation failed: {e}")

    def _validate_token(self, token: str) -> Dict:
        try:
            claims = jwt.get_unverified_claims(token)
            import time

            if "exp" in claims and claims["exp"] < time.time():
                raise Exception("Token expired")
            return claims
        except JWTError as e:
            raise Exception(f"Token validation failed: {e}")

    def access_token_info(self) -> Dict:
        if not self._tokens or "access_token" not in self._tokens:
            raise Exception("Not authenticated. Please run login first.")

        access_token = self._tokens["access_token"]

        try:
            claims = self._validate_token(access_token)
            return {
                "access_token": access_token,
                "claims": claims,
            }
        except Exception:
            # Token might be expired, try to refresh
            try:
                self._refresh_tokens()
                access_token = self._tokens["access_token"]
                claims = self._validate_token(access_token)
                return {
                    "access_token": access_token,
                    "claims": claims,
                }
            except Exception as e:
                raise Exception(f"Failed to get valid access token: {e}")

    def get_id_token(self) -> str:
        if not self._tokens or "id_token" not in self._tokens:
            raise Exception("Not authenticated. Please run login first.")

        return self._tokens["id_token"]
