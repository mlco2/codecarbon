import io
import json
import unittest
from unittest.mock import MagicMock, patch

from codecarbon.cli import auth
from codecarbon.cli.auth import _CallbackHandler


class TestCallbackHandler(unittest.TestCase):
    def setUp(self):
        self.handler = _CallbackHandler
        self.handler.callback_url = None
        self.handler.error = None

    def _make_handler(self, path):
        # Simulate BaseHTTPRequestHandler environment
        request = MagicMock()
        request.makefile.return_value = io.BytesIO()
        server = MagicMock()
        handler = _CallbackHandler(request, ("127.0.0.1", 12345), server)
        handler.path = path
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.log_message = MagicMock()
        return handler

    def test_do_get_success(self):
        handler = self._make_handler("/callback?code=abc123&state=xyz")
        handler.do_GET()
        # Should set callback_url and not error
        self.assertIsNone(_CallbackHandler.error)
        self.assertTrue(
            _CallbackHandler.callback_url.endswith("/callback?code=abc123&state=xyz")
        )
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "text/html")
        handler.end_headers.assert_called()
        output = handler.wfile.getvalue().decode()
        self.assertIn("Login successful", output)

    def test_do_get_error(self):
        handler = self._make_handler(
            "/callback?error=access_denied&error_description=User+denied+access"
        )
        handler.do_GET()
        # Should set error and not callback_url
        self.assertEqual(_CallbackHandler.error, "access_denied")
        handler.send_response.assert_called_with(400)
        handler.send_header.assert_called_with("Content-Type", "text/html")
        handler.end_headers.assert_called()
        output = handler.wfile.getvalue().decode()
        self.assertIn("Login failed", output)
        self.assertIn("User denied access", output)


class TestAuthMethods(unittest.TestCase):
    @patch("codecarbon.cli.auth.requests.get")
    def test_discover_endpoints(self, mock_get):
        mock_get.return_value.json.return_value = {
            "token_endpoint": "url",
            "jwks_uri": "jwks",
        }
        mock_get.return_value.raise_for_status.return_value = None
        result = auth._discover_endpoints()
        self.assertIn("token_endpoint", result)
        self.assertIn("jwks_uri", result)

    @patch("builtins.open")
    def test_save_and_load_credentials(self, mock_open):
        # Save
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        tokens = {"access_token": "a", "refresh_token": "r", "id_token": "i"}
        auth._save_credentials(tokens)
        mock_file.write.assert_called()
        # Load
        mock_file.read.return_value = json.dumps(tokens)
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.__iter__.return_value = iter([json.dumps(tokens)])
        mock_file.read.return_value = json.dumps(tokens)
        with patch("json.load", return_value=tokens):
            loaded = auth._load_credentials()
            self.assertEqual(loaded, tokens)

    @patch("codecarbon.cli.auth.requests.get")
    @patch("codecarbon.cli.auth.JsonWebKey.import_key_set")
    @patch("codecarbon.cli.auth.jose_jwt.decode")
    def test_validate_access_token_valid(
        self, mock_decode, mock_import_key_set, mock_get
    ):
        mock_get.return_value.json.return_value = {"jwks_uri": "jwks"}
        mock_get.return_value.raise_for_status.return_value = None
        mock_import_key_set.return_value = "keyset"
        mock_decode.return_value.validate.return_value = None
        with patch(
            "codecarbon.cli.auth._discover_endpoints", return_value={"jwks_uri": "jwks"}
        ):
            self.assertTrue(auth._validate_access_token("token"))

    @patch("codecarbon.cli.auth.requests.post")
    @patch("codecarbon.cli.auth._discover_endpoints")
    def test_refresh_tokens(self, mock_discover, mock_post):
        mock_discover.return_value = {"token_endpoint": "url"}
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {
            "access_token": "a",
            "refresh_token": "r",
        }
        result = auth._refresh_tokens("refresh")
        self.assertIn("access_token", result)
        self.assertIn("refresh_token", result)

    @patch("codecarbon.cli.auth._load_credentials")
    @patch("codecarbon.cli.auth._validate_access_token")
    def test_get_access_token_valid(self, mock_validate, mock_load):
        mock_load.return_value = {"access_token": "a", "refresh_token": "r"}
        mock_validate.return_value = True
        self.assertEqual(auth.get_access_token(), "a")

    @patch("codecarbon.cli.auth._load_credentials")
    @patch("codecarbon.cli.auth._validate_access_token")
    @patch("codecarbon.cli.auth._refresh_tokens")
    @patch("codecarbon.cli.auth._save_credentials")
    def test_get_access_token_refresh(
        self, mock_save, mock_refresh, mock_validate, mock_load
    ):
        mock_load.return_value = {"access_token": "a", "refresh_token": "r"}
        mock_validate.return_value = False
        mock_refresh.return_value = {"access_token": "b", "refresh_token": "r"}
        self.assertEqual(auth.get_access_token(), "b")
        mock_save.assert_called()

    @patch("codecarbon.cli.auth._load_credentials")
    def test_get_id_token(self, mock_load):
        mock_load.return_value = {"id_token": "i"}
        self.assertEqual(auth.get_id_token(), "i")


if __name__ == "__main__":
    unittest.main()
