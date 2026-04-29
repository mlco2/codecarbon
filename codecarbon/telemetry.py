TELEMETRY_API_KEY = "cpt_sDiIpdwl5BRUM2T6vIJrt2JjL-pB3b46v8cvpLwuroU"
TELEMETRY_API_URL = "https://api.codecarbon.io"
TELEMETRY_EXPERIMENT_ID = None  # Set before enabling Tier 2 (see Task 4)

_TIER1_SENT = False  # module-level dedup: send once per Python session

_TIER1_FIELDS = [
    "python_version",
    "os",
    "cpu_count",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "ram_total_size",
    "codecarbon_version",
    "tracking_mode",
]


def collect_tier1_payload(conf: dict) -> dict:
    return {k: conf.get(k) for k in _TIER1_FIELDS}
