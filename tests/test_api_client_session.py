"""
Connection-reuse and timeout tests for ApiClient.

These run against a stdlib HTTP server on loopback rather than requests_mock,
because requests_mock replaces the transport adapter and therefore never opens
a real connection, which is exactly what is under test here. No traffic leaves
the machine.
"""

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from codecarbon.core.api_client import ApiClient

CONF = {
    "os": "linux",
    "python_version": "3.12",
    "codecarbon_version": "3.0",
    "cpu_count": 8,
    "cpu_model": "CPU",
    "gpu_count": 0,
    "gpu_model": "",
    "longitude": 0.0,
    "latitude": 0.0,
    "region": "EU",
    "provider": "none",
    "ram_total_size": 16.0,
    "tracking_mode": "machine",
}

EMISSION = {
    "duration": 5,
    "emissions": 1.0,
    "emissions_rate": 1.0,
    "cpu_power": 1.0,
    "gpu_power": 0.0,
    "ram_power": 0.5,
    "cpu_energy": 0.1,
    "gpu_energy": 0.0,
    "ram_energy": 0.1,
    "energy_consumed": 0.2,
}


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # keep-alive, so pooling is observable

    def log_message(self, *args):
        pass

    def _serve(self):
        self.server.state["requests"] += 1
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        body = b'{"id": "run-1"}'
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _serve
    do_POST = _serve


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, state):
        self.state = state
        super().__init__(("127.0.0.1", 0), _Handler)

    def process_request(self, request, client_address):
        self.state["connections"] += 1
        super().process_request(request, client_address)


class TestSessionReuse(unittest.TestCase):
    def setUp(self):
        self.state = {"requests": 0, "connections": 0}
        self.server = _Server(self.state)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.api = ApiClient(
            endpoint_url=self.url,
            experiment_id="exp-1",
            conf=CONF,
            create_run_automatically=False,
        )
        self.addCleanup(self.api.close)
        self.api.run_id = "run-1"

    def test_sequential_calls_reuse_one_connection(self):
        for _ in range(50):
            self.assertTrue(self.api.add_emission(dict(EMISSION)))

        self.assertEqual(self.state["requests"], 50)
        self.assertEqual(self.state["connections"], 1)

    def test_close_is_idempotent(self):
        self.api.add_emission(dict(EMISSION))
        self.api.close()
        self.api.close()


class TestTimeout(unittest.TestCase):
    def test_requests_get_a_connect_and_read_timeout(self):
        api = ApiClient(endpoint_url="http://test.com", create_run_automatically=False)
        self.addCleanup(api.close)
        seen = {}

        def fake_get(url, json, timeout, headers):
            seen["timeout"] = timeout
            return type("R", (), {"status_code": 200, "json": lambda self: {}})()

        api._request(fake_get, "http://test.com/x")
        self.assertEqual(seen["timeout"], (3.05, 10))


if __name__ == "__main__":
    unittest.main()
