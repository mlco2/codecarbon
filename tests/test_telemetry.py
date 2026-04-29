import sys
import platform
from codecarbon.telemetry import collect_tier1_payload


def test_collect_tier1_payload_has_required_fields():
    conf = {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "cpu_count": 8,
        "cpu_model": "Intel Core i7",
        "gpu_count": 1,
        "gpu_model": "NVIDIA RTX 3080",
        "ram_total_size": 32.0,
        "codecarbon_version": "2.0.0",
        "tracking_mode": "machine",
    }
    payload = collect_tier1_payload(conf)
    assert "python_version" in payload
    assert "os" in payload
    assert "cpu_count" in payload
    assert "cpu_model" in payload
    assert "gpu_count" in payload
    assert "gpu_model" in payload
    assert "ram_total_size" in payload
    assert "codecarbon_version" in payload
    assert "tracking_mode" in payload
    assert payload["python_version"] == conf["python_version"]
