"""
LLM energy benchmark harness.

Implements the measurement procedure defined in
``specs/llm-energy-benchmark-v1.md`` and emits a BoAmps report describing the
result. See ``codecarbon.benchmark.runner.run_benchmark`` for the entry point.
"""

from codecarbon.benchmark.backends import (  # noqa: F401
    Backend,
    BackendInfo,
    GenerationResult,
    OllamaBackend,
    OpenAICompatibleBackend,
    get_backend,
)
from codecarbon.benchmark.record import build_boamps_record  # noqa: F401
from codecarbon.benchmark.runner import (  # noqa: F401
    BenchmarkConfig,
    BenchmarkResult,
    WindowResult,
    run_benchmark,
)
from codecarbon.benchmark.upload import UploadError, upload_record  # noqa: F401
from codecarbon.benchmark.validation import (  # noqa: F401
    SPEC_VERSION,
    ValidationError,
    validate_record,
)
