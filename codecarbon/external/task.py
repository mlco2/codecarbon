import time
from uuid import uuid4

from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData


def _get(response, *names):
    """
    Read the first available attribute or mapping key from ``response``.
    Returns None if none of ``names`` is present.
    """
    for name in names:
        if isinstance(response, dict):
            value = response.get(name)
        else:
            value = getattr(response, name, None)
        if value is not None:
            return value
    return None


def extract_token_counts(response):
    """
    Best effort extraction of (input_tokens, output_tokens) from the response of
    an LLM serving stack. Everything is duck-typed, so codecarbon does not import
    any inference library:

    - OpenAI compatible clients : ``usage.prompt_tokens`` / ``usage.completion_tokens``
    - Ollama : ``prompt_eval_count`` / ``eval_count``
    - vLLM ``RequestOutput`` : ``prompt_token_ids`` / ``outputs[].token_ids``

    Counts that cannot be found are reported as 0.
    """
    usage = _get(response, "usage")
    if usage is not None:
        return (
            _get(usage, "prompt_tokens", "input_tokens") or 0,
            _get(usage, "completion_tokens", "output_tokens") or 0,
        )

    eval_count = _get(response, "eval_count")
    if eval_count is not None:
        return _get(response, "prompt_eval_count") or 0, eval_count

    prompt_token_ids = _get(response, "prompt_token_ids")
    if prompt_token_ids is not None:
        outputs = _get(response, "outputs") or []
        return (
            len(prompt_token_ids),
            sum(len(getattr(completion, "token_ids", ())) for completion in outputs),
        )

    return 0, 0


class Task:
    """
    A task, used to segregate electrical consumption when executing a treatment.
    """

    is_active: bool
    emissions_data: EmissionsData

    def __init__(self, task_name):  # , task_measure
        self.task_id: str = task_name + uuid4().__str__()
        self.task_name: str = task_name
        self.start_time = time.perf_counter()
        self.is_active = True
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.n_requests: int = 0

    def record_tokens(
        self, input_tokens: int = 0, output_tokens: int = 0, n_requests: int = 1
    ) -> None:
        """
        Accumulate token counters for this task.
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.n_requests += n_requests

    def out(self):
        return TaskEmissionsData(
            task_name=self.task_name,
            timestamp=self.emissions_data.timestamp,
            project_name=self.emissions_data.project_name,
            run_id=self.emissions_data.run_id,
            duration=self.emissions_data.duration,
            emissions=self.emissions_data.emissions,
            emissions_rate=self.emissions_data.emissions_rate,
            cpu_power=self.emissions_data.cpu_power,
            gpu_power=self.emissions_data.gpu_power,
            ram_power=self.emissions_data.ram_power,
            cpu_energy=self.emissions_data.cpu_energy,
            gpu_energy=self.emissions_data.gpu_energy,
            ram_energy=self.emissions_data.ram_energy,
            energy_consumed=self.emissions_data.energy_consumed,
            water_consumed=self.emissions_data.water_consumed,
            country_name=self.emissions_data.country_name,
            country_iso_code=self.emissions_data.country_iso_code,
            region=self.emissions_data.region,
            cloud_provider=self.emissions_data.cloud_provider,
            cloud_region=self.emissions_data.cloud_region,
            os=self.emissions_data.os,
            python_version=self.emissions_data.python_version,
            codecarbon_version=self.emissions_data.codecarbon_version,
            cpu_count=self.emissions_data.cpu_count,
            cpu_model=self.emissions_data.cpu_model,
            gpu_count=self.emissions_data.gpu_count,
            gpu_model=self.emissions_data.gpu_model,
            longitude=self.emissions_data.longitude,
            latitude=self.emissions_data.latitude,
            ram_total_size=self.emissions_data.ram_total_size,
            tracking_mode=self.emissions_data.tracking_mode,
            on_cloud=self.emissions_data.on_cloud,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            n_requests=self.n_requests,
        )
