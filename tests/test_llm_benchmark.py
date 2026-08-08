"""
Tests for the LLM energy benchmark harness.

None of these need a serving engine or a GPU: the backends are exercised
against mocked HTTP, and the runner's analysis is tested on synthetic windows.
"""

import json
import unittest

import requests_mock

from codecarbon.benchmark.backends import (
    OllamaBackend,
    OpenAICompatibleBackend,
    get_backend,
)
from codecarbon.benchmark.prompts import build_prompt, build_prompts, load_prompt_set
from codecarbon.benchmark.record import ModelMetadata, build_boamps_record
from codecarbon.benchmark.runner import (
    BenchmarkConfig,
    WindowResult,
    _size_window,
    _summarise,
)
from codecarbon.benchmark.validation import SPEC_VERSION, validate_record


def _emissions_data(duration=140.0, cpu=0.004, gpu=0.012, ram=0.0006):
    from codecarbon.output_methods.emissions_data import EmissionsData

    return EmissionsData(
        timestamp="2026-08-08T13:20:00",
        project_name="codecarbon-llm-benchmark",
        run_id="11111111-1111-1111-1111-111111111111",
        experiment_id="22222222-2222-2222-2222-222222222222",
        duration=duration,
        emissions=0.001,
        emissions_rate=0.00001,
        cpu_power=120.0,
        gpu_power=300.0,
        ram_power=10.0,
        cpu_energy=cpu,
        gpu_energy=gpu,
        ram_energy=ram,
        energy_consumed=cpu + gpu + ram,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="ile-de-france",
        cloud_provider="",
        cloud_region="",
        os="Linux-6.1",
        python_version="3.11.0",
        codecarbon_version="3.0.6",
        cpu_count=64,
        cpu_model="AMD EPYC 7763 64-Core Processor",
        gpu_count=1,
        gpu_model="1 x NVIDIA A100-SXM4-80GB",
        longitude=2.35,
        latitude=48.85,
        ram_total_size=512.0,
        tracking_mode="machine",
        cpu_utilization_percent=45.0,
        gpu_utilization_percent=92.0,
    )


def _window(energy_scale=1.0, output_tokens=163840, duration=140.0):
    data = _emissions_data(
        duration=duration,
        cpu=0.004 * energy_scale,
        gpu=0.012 * energy_scale,
        ram=0.0006 * energy_scale,
    )
    return WindowResult(
        duration_s=duration,
        n_requests=640,
        input_tokens=84000,
        output_tokens=output_tokens,
        cpu_energy_kwh=data.cpu_energy,
        gpu_energy_kwh=data.gpu_energy,
        ram_energy_kwh=data.ram_energy,
        cpu_utilization_percent=45.0,
        gpu_utilization_percent=92.0,
        ttft_p50_s=0.21,
        tps_per_request_p50=41.6,
        short_requests=0,
        emissions_data=data,
    )


class _FakeBackendInfo:
    name = "vllm"
    version = "0.6.3"
    supports_forced_output_length = True
    tensor_parallel_size = 1
    prefix_caching_disabled = True


def _result(windows=None, backend_info=None):
    config = BenchmarkConfig(model="test-model", concurrency=64)
    windows = windows or [_window(), _window(1.02), _window(0.99)]
    return _summarise(
        config,
        backend_info or _FakeBackendInfo(),
        windows,
        _window(0.05, output_tokens=0, duration=30.0),
        _window(0.05, output_tokens=0, duration=30.0),
        cpu_tracking_mode="intel_rapl",
        gpu_tracking_mode="nvml",
    )


class TestPrompts(unittest.TestCase):
    def test_prompt_set_loads(self):
        prompts = load_prompt_set("v1")
        self.assertEqual(len(prompts), 64)
        self.assertTrue(all(p.strip() for p in prompts))

    def test_prompts_are_deterministic(self):
        first = build_prompts(10, 128)
        second = build_prompts(10, 128)
        self.assertEqual(first, second)

    def test_prefixes_are_unique(self):
        """
        Engines with automatic prefix caching would skip input processing for
        shared prefixes, so the benchmark would measure the cache. Every prompt
        must differ from the very first tokens.
        """
        prompts = build_prompts(200, 128)
        prefixes = {p[:32] for p in prompts}
        self.assertEqual(len(prefixes), len(prompts))

    def test_larger_bucket_produces_longer_prompt(self):
        short = build_prompts(1, 128)[0]
        long = build_prompts(1, 1024)[0]
        self.assertGreater(len(long.split()), len(short.split()) * 3)

    def test_build_prompt_without_context_is_safe(self):
        prompt = build_prompt(0, ["Explain caching."], [], 128)
        self.assertIn("Explain caching.", prompt)


class TestOpenAIBackend(unittest.TestCase):
    def _backend(self, m, forced=True):
        m.get("http://engine/version", json={"version": "0.6.3"})
        m.get("http://engine/v1/version", json={"version": "0.6.3"})
        m.post(
            "http://engine/v1/completions",
            status_code=200 if forced else 400,
            json={},
        )
        return OpenAICompatibleBackend(base_url="http://engine", model="m")

    def test_probe_detects_forced_length_support(self):
        with requests_mock.Mocker() as m:
            backend = self._backend(m, forced=False)
            self.assertFalse(backend.info().supports_forced_output_length)

    def test_generate_parses_stream(self):
        with requests_mock.Mocker() as m:
            backend = self._backend(m)
            stream = (
                'data: {"choices":[{"text":"a","finish_reason":null}]}\n'
                'data: {"choices":[{"text":"b","finish_reason":"length"}]}\n'
                'data: {"choices":[],"usage":'
                '{"prompt_tokens":131,"completion_tokens":256}}\n'
                "data: [DONE]\n"
            )
            m.post("http://engine/v1/completions", text=stream)
            result = backend.generate("hello", 256)

        self.assertEqual(result.input_tokens, 131)
        self.assertEqual(result.output_tokens, 256)
        self.assertTrue(result.length_capped)
        self.assertIsNotNone(result.ttft_s)


class TestOllamaBackend(unittest.TestCase):
    def test_generate_parses_stream(self):
        with requests_mock.Mocker() as m:
            stream = (
                '{"response":"a","done":false}\n'
                '{"response":"","done":true,"done_reason":"length",'
                '"prompt_eval_count":120,"eval_count":256}\n'
            )
            m.post("http://ollama/api/generate", text=stream)
            backend = OllamaBackend(base_url="http://ollama", model="m")
            result = backend.generate("hello", 256)

        self.assertEqual(result.input_tokens, 120)
        self.assertEqual(result.output_tokens, 256)
        self.assertTrue(result.length_capped)

    def test_ollama_cannot_force_output_length(self):
        """Spec §3.6 is unsatisfiable on Ollama; the record must say so."""
        with requests_mock.Mocker() as m:
            m.get("http://ollama/api/version", json={"version": "0.5.0"})
            backend = OllamaBackend(base_url="http://ollama", model="m")
            self.assertFalse(backend.info().supports_forced_output_length)

    def test_get_backend_rejects_unknown(self):
        with self.assertRaises(ValueError):
            get_backend("not-a-backend", model="m")


class TestWindowSizing(unittest.TestCase):
    def test_sized_to_clear_both_minimums(self):
        config = BenchmarkConfig(model="m", concurrency=8, output_tokens=256)
        n = _size_window(config, observed_tps=2000.0)
        # 120s at 2000 tok/s needs 240000 tokens -> ~937 requests of 256.
        self.assertGreater(n * 256, config.min_output_tokens)
        self.assertGreater(n, 900)

    def test_never_below_concurrency(self):
        config = BenchmarkConfig(model="m", concurrency=64, output_tokens=256)
        self.assertGreaterEqual(_size_window(config, observed_tps=0.0), 64)


class TestSummarise(unittest.TestCase):
    def test_clean_run_passes_all_gates(self):
        result = _result()
        self.assertEqual(result.gate_failures, [])
        self.assertTrue(result.passed)
        self.assertLess(result.relative_spread, 0.15)

    def test_median_window_is_a_real_window(self):
        """
        The record must describe a run that happened. Averaging energy and
        tokens across windows would describe none of them.
        """
        result = _result()
        self.assertIn(result.median_window, result.windows)

    def test_noisy_run_fails_repeatability(self):
        result = _result(windows=[_window(1.0), _window(2.0), _window(1.1)])
        self.assertTrue(
            any("repeatability" in f for f in result.gate_failures),
            result.gate_failures,
        )

    def test_short_window_fails(self):
        windows = [_window(duration=30.0) for _ in range(3)]
        result = _result(windows=windows)
        self.assertTrue(any("below" in f for f in result.gate_failures))

    def test_unforced_output_length_fails(self):
        info = _FakeBackendInfo()
        info.supports_forced_output_length = False
        result = _result(backend_info=info)
        self.assertTrue(
            any("output length not forced" in f for f in result.gate_failures)
        )


class TestRecord(unittest.TestCase):
    def setUp(self):
        self.metadata = ModelMetadata(
            name="mistralai/Mistral-7B-Instruct-v0.3",
            parameters_number=7.25,
            quantization="fp16",
            uri="https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3",
            revision="e0bc86c",
            tensor_parallel_size=1,
        )
        self.record = build_boamps_record(
            _result(), self.metadata, publisher_name="Data For Good"
        )

    def test_rejects_free_text_quantization(self):
        with self.assertRaises(ValueError):
            ModelMetadata(name="m", parameters_number=7.0, quantization="q16")

    def test_record_is_json_serialisable(self):
        json.dumps(self.record)

    def test_profile_required_fields(self):
        self.assertEqual(self.record["task"]["taskStage"], "inference")
        self.assertEqual(self.record["task"]["algorithms"][0]["algorithmType"], "llm")
        self.assertEqual(
            self.record["header"]["publisher"]["confidentialityLevel"], "public"
        )

    def test_tracking_modes_are_populated(self):
        """CodeCarbon's exporter omits these; the harness must fill them in."""
        measure = self.record["measures"][0]
        self.assertEqual(measure["cpuTrackingMode"], "intel_rapl")
        self.assertEqual(measure["gpuTrackingMode"], "nvml")

    def test_calibration_is_recorded_not_subtracted(self):
        measure = self.record["measures"][0]
        self.assertGreater(measure["powerCalibrationMeasurement"], 0)
        breakdown = self.record["llmBenchmark"]["energyBreakdownKwh"]
        self.assertAlmostEqual(
            sum(breakdown.values()), measure["powerConsumption"], places=9
        )

    def test_components_declare_share(self):
        for component in self.record["infrastructure"]["components"]:
            self.assertEqual(component["share"], 1)

    def test_token_counts_are_totals(self):
        dataset = {d["dataUsage"]: d for d in self.record["task"]["dataset"]}
        self.assertEqual(dataset["output"]["dataQuantity"], 163840)
        self.assertEqual(dataset["input"]["dataQuantity"], 84000)

    def test_facility_pue_is_metadata_not_a_multiplier(self):
        record = build_boamps_record(
            _result(), self.metadata, publisher_name="DFG", facility_pue=1.3
        )
        self.assertEqual(record["llmBenchmark"]["facilityPue"], 1.3)
        self.assertEqual(
            record["measures"][0]["powerConsumption"],
            self.record["measures"][0]["powerConsumption"],
        )


class TestValidation(unittest.TestCase):
    def setUp(self):
        metadata = ModelMetadata(
            name="m", parameters_number=7.0, quantization="fp16", revision="abc"
        )
        self.record = build_boamps_record(
            _result(), metadata, publisher_name="Data For Good"
        )

    def test_generated_record_is_valid(self):
        self.assertEqual(validate_record(self.record), [])

    def test_unknown_spec_version_rejected(self):
        record = dict(self.record)
        record["llmBenchmark"] = dict(record["llmBenchmark"], specVersion="9.9.9")
        self.assertTrue(any("rule 8" in f for f in validate_record(record)))

    def test_short_window_rejected(self):
        record = dict(self.record)
        record["measures"] = [dict(record["measures"][0], measurementDuration=10)]
        self.assertTrue(any("rule 2" in f for f in validate_record(record)))

    def test_shared_hardware_rejected(self):
        record = dict(self.record)
        components = [dict(c) for c in record["infrastructure"]["components"]]
        components[0]["share"] = 0.5
        record["infrastructure"] = dict(record["infrastructure"], components=components)
        self.assertTrue(any("rule 9" in f for f in validate_record(record)))

    def test_energy_breakdown_must_sum(self):
        record = dict(self.record)
        breakdown = dict(record["llmBenchmark"]["energyBreakdownKwh"], gpu=99.0)
        record["llmBenchmark"] = dict(
            record["llmBenchmark"], energyBreakdownKwh=breakdown
        )
        self.assertTrue(any("rule 7" in f for f in validate_record(record)))

    def test_unforced_output_length_rejected(self):
        record = dict(self.record)
        record["llmBenchmark"] = dict(record["llmBenchmark"], forcedOutputLength=False)
        self.assertTrue(any("rule 5" in f for f in validate_record(record)))

    def test_spec_version_matches_harness(self):
        self.assertEqual(self.record["llmBenchmark"]["specVersion"], SPEC_VERSION)


if __name__ == "__main__":
    unittest.main()
