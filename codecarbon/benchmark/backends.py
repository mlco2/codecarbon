"""
Serving-engine backends for the LLM energy benchmark.

A backend drives generation and reports authoritative token counts. The harness
owns the generation loop rather than wrapping an opaque user command, because
energy per output token is only meaningful with a trustworthy token count
(spec §7.2).

All backends stream, so time-to-first-token is measured rather than inferred.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from codecarbon.external.logger import logger

DEFAULT_TIMEOUT = 600


@dataclass
class GenerationResult:
    """Outcome of a single generation request."""

    input_tokens: int
    output_tokens: int
    latency_s: float
    ttft_s: Optional[float]
    length_capped: bool  # True if generation stopped because the cap was hit


@dataclass
class BackendInfo:
    """Static description of the serving engine, for the BoAmps record."""

    name: str
    version: str
    supports_forced_output_length: bool
    tensor_parallel_size: Optional[int] = None
    prefix_caching_disabled: Optional[bool] = None


class Backend(ABC):
    """Interface every serving engine adapter implements."""

    @abstractmethod
    def info(self) -> BackendInfo:
        """Engine name, version and capabilities."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> GenerationResult:
        """Run one request to completion and return its measured result."""

    def close(self) -> None:
        """Release any held resources."""


def _stream_lines(response: requests.Response):
    for raw in response.iter_lines():
        if raw:
            yield raw.decode("utf-8")


class OpenAICompatibleBackend(Backend):
    """
    Backend for any engine exposing the OpenAI ``/v1/completions`` API.

    Covers vLLM, TGI, llama.cpp's server and SGLang. Uses the completions
    endpoint rather than chat completions so that the prompt is sent verbatim
    and the input token count is not perturbed by a chat template.

    ``ignore_eos`` and ``min_tokens`` are vLLM extensions. When the engine
    accepts them, output length is genuinely forced and spec §3.6 is satisfied;
    ``supports_forced_output_length`` reflects whether the probe succeeded.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str = "",
        api_key: Optional[str] = None,
        engine_name: str = "vllm",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.engine_name = engine_name
        self._session = requests.Session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"
        self._forced_length = self._probe_forced_length()

    def _probe_forced_length(self) -> bool:
        """Check whether the engine honours ignore_eos, with a 1-token request."""
        try:
            resp = self._session.post(
                f"{self.base_url}/v1/completions",
                json={
                    "model": self.model,
                    "prompt": "probe",
                    "max_tokens": 1,
                    "temperature": 0,
                    "ignore_eos": True,
                    "min_tokens": 1,
                },
                timeout=60,
            )
            return resp.status_code == 200
        except requests.RequestException as exc:
            logger.warning("Forced-output-length probe failed: %s", exc)
            return False

    def _engine_version(self) -> str:
        """
        Read the engine version from whichever endpoint the server exposes.

        vLLM answers /version; llama.cpp has no version endpoint but reports a
        build id as `system_fingerprint` on every completion, which /props also
        carries via `build_info` on newer builds. The version identifies the
        kernels that produced the measurement, so "unknown" is a real loss of
        provenance rather than a cosmetic gap.
        """
        for path in ("/version", "/v1/version"):
            try:
                resp = self._session.get(f"{self.base_url}{path}", timeout=30)
                if resp.status_code == 200:
                    body = resp.json()
                    if isinstance(body, dict):
                        version = body.get("version")
                        if version:
                            return str(version)
            except (requests.RequestException, ValueError):
                continue
        fingerprint = self._probe_fingerprint()
        return fingerprint or "unknown"

    def _probe_fingerprint(self) -> Optional[str]:
        """llama.cpp reports its build id as system_fingerprint on completions."""
        try:
            resp = self._session.post(
                f"{self.base_url}/v1/completions",
                json={
                    "model": self.model,
                    "prompt": "probe",
                    "max_tokens": 1,
                    "temperature": 0,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json().get("system_fingerprint")
        except (requests.RequestException, ValueError):
            pass
        return None

    def info(self) -> BackendInfo:
        return BackendInfo(
            name=self.engine_name,
            version=self._engine_version(),
            supports_forced_output_length=self._forced_length,
        )

    def generate(self, prompt: str, max_tokens: int) -> GenerationResult:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if self._forced_length:
            payload["ignore_eos"] = True
            payload["min_tokens"] = max_tokens

        start = time.perf_counter()
        ttft: Optional[float] = None
        usage: Dict[str, Any] = {}
        finish_reason: Optional[str] = None

        with self._session.post(
            f"{self.base_url}/v1/completions",
            json=payload,
            stream=True,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            for line in _stream_lines(resp):
                if not line.startswith("data: "):
                    continue
                data = line[len("data: ") :]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if choices and ttft is None and choices[0].get("text"):
                    ttft = time.perf_counter() - start
                if choices and choices[0].get("finish_reason"):
                    finish_reason = choices[0]["finish_reason"]
                if chunk.get("usage"):
                    usage = chunk["usage"]

        latency = time.perf_counter() - start
        return GenerationResult(
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_s=latency,
            ttft_s=ttft,
            length_capped=finish_reason == "length",
        )


class OllamaBackend(Backend):
    """
    Backend for Ollama's native ``/api/generate`` API.

    Ollama has no ``ignore_eos`` equivalent: ``num_predict`` is an upper bound,
    and the model still stops at EOS. Output length therefore cannot be forced,
    so ``supports_forced_output_length`` is False and records produced with this
    backend fail spec §3.6 (validity rule 5).

    Requests that stop early are still counted, in both energy and tokens —
    the energy was spent either way, and dropping their tokens while keeping
    their energy would inflate the per-token figure. The runner reports how
    many stopped short so the shortfall is visible.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._session = requests.Session()

    def _engine_version(self) -> str:
        try:
            resp = self._session.get(f"{self.base_url}/api/version", timeout=30)
            if resp.status_code == 200:
                return str(resp.json().get("version", "unknown"))
        except (requests.RequestException, ValueError):
            pass
        return "unknown"

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="ollama",
            version=self._engine_version(),
            supports_forced_output_length=False,
        )

    def generate(self, prompt: str, max_tokens: int) -> GenerationResult:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0,
                "seed": 0,
            },
        }

        start = time.perf_counter()
        ttft: Optional[float] = None
        final: Dict[str, Any] = {}

        with self._session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            stream=True,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            for line in _stream_lines(resp):
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ttft is None and chunk.get("response"):
                    ttft = time.perf_counter() - start
                if chunk.get("done"):
                    final = chunk

        latency = time.perf_counter() - start
        output_tokens = int(final.get("eval_count", 0))
        return GenerationResult(
            input_tokens=int(final.get("prompt_eval_count", 0)),
            output_tokens=output_tokens,
            latency_s=latency,
            ttft_s=ttft,
            # Ollama reports done_reason="length" when num_predict was reached.
            length_capped=final.get("done_reason") == "length"
            or output_tokens >= max_tokens,
        )


_BACKENDS = {
    "vllm": lambda **kw: OpenAICompatibleBackend(engine_name="vllm", **kw),
    # llama.cpp's server speaks the same /v1/completions API and honours
    # ignore_eos, so it needs no separate adapter -- only its own name, since
    # the engine is part of what the measurement describes.
    "llama-cpp": lambda **kw: OpenAICompatibleBackend(engine_name="llama.cpp", **kw),
    "openai-compatible": lambda **kw: OpenAICompatibleBackend(
        engine_name="openai-compatible", **kw
    ),
    "ollama": lambda **kw: OllamaBackend(**kw),
}


def get_backend(name: str, **kwargs) -> Backend:
    """Instantiate a backend by name."""
    if name not in _BACKENDS:
        raise ValueError(
            f"Unknown backend '{name}'. Available: {', '.join(sorted(_BACKENDS))}"
        )
    if name == "ollama":
        kwargs.pop("api_key", None)
        kwargs.setdefault("base_url", "http://localhost:11434")
    return _BACKENDS[name](**kwargs)
