"""
Live local dashboard.

An output handler that keeps a bounded window of live measurements in memory and
serves them, with a single self-contained HTML page, over a stdlib HTTP server.
No dependency, no database, no network access: it is meant for watching a run on
the machine that is being measured.
"""

import dataclasses
import json
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import List

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData

# Fields kept for every sample. The rest of EmissionsData is either static
# (hardware, geography) or not useful on a live chart.
SAMPLE_FIELDS = (
    "timestamp",
    "duration",
    "cpu_power",
    "gpu_power",
    "ram_power",
    "energy_consumed",
    "cpu_utilization_percent",
    "gpu_utilization_percent",
    "ram_utilization_percent",
)

METADATA_FIELDS = (
    "project_name",
    "experiment_id",
    "run_id",
    "cpu_count",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "ram_total_size",
    "country_name",
    "country_iso_code",
    "region",
    "os",
    "python_version",
    "codecarbon_version",
    "tracking_mode",
)


def _page() -> bytes:
    return resources.files("codecarbon.viz").joinpath("live.html").read_bytes()


class LiveDashboardOutput(BaseOutput):
    """
    Serve a live view of the current run on http://<host>:<port>.

    Usage::

        tracker = EmissionsTracker(output_handlers=[LiveDashboardOutput()])

    The handler keeps at most ``history`` samples in memory, so it is safe to
    leave running for days. If the port is already taken the handler logs an
    error and stays inert: a busy port must never take down a measurement run.
    """

    live_out_every_measure = True

    def __init__(self, port: int = 8050, host: str = "127.0.0.1", history: int = 720):
        self.port = port
        self.host = host
        self._history = deque(maxlen=history)
        self._metadata = {}
        self._tasks = []
        self._lock = threading.Lock()
        self._server = None
        self._start_server()

    def _start_server(self) -> None:
        handler_self = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # http.server API naming
                if self.path.startswith("/data"):
                    self._respond(
                        200, "application/json", handler_self._snapshot().encode()
                    )
                elif self.path.startswith("/health"):
                    self._respond(200, "application/json", b'{"status": "ok"}')
                elif self.path == "/":
                    self._respond(200, "text/html; charset=utf-8", _page())
                else:
                    self._respond(404, "text/plain", b"not found")

            def _respond(self, status, content_type, body):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                """Silence the default stderr access log."""

        try:
            self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError as e:
            logger.error(
                f"Live dashboard could not bind {self.host}:{self.port} ({e}). "
                "Continuing without the live dashboard."
            )
            return

        # The OS assigns the port when 0 was requested, so report the real one.
        self.port = self._server.server_address[1]
        if self.host not in ("127.0.0.1", "localhost", "::1"):
            logger.warning(
                f"Live dashboard is listening on {self.host}:{self.port} and is "
                "not authenticated. Prefer 127.0.0.1 with SSH port forwarding."
            )
        threading.Thread(
            target=self._server.serve_forever, daemon=True, name="codecarbon-live-ui"
        ).start()
        logger.info(f"Live dashboard available on http://{self.host}:{self.port}")

    @property
    def is_serving(self) -> bool:
        return self._server is not None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _snapshot(self) -> str:
        with self._lock:
            return json.dumps(
                {
                    "samples": list(self._history),
                    "metadata": self._metadata,
                    "tasks": self._tasks,
                }
            )

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        values = total.values
        sample = {k: values[k] for k in SAMPLE_FIELDS}
        # Grams are what a human reads; kg is what the dataclass carries.
        sample["emissions_g"] = total.emissions * 1000
        with self._lock:
            self._history.append(sample)
            self._metadata = {k: values[k] for k in METADATA_FIELDS}

    def out(self, total: EmissionsData, delta: EmissionsData):
        self.live_out(total, delta)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        tasks = [dataclasses.asdict(task) for task in data]
        with self._lock:
            self._tasks = tasks

    def exit(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
