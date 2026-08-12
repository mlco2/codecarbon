# CodeCarbon examples

Runnable scripts and notebooks showing how to track emissions in real workloads.

This README is the canonical index of this directory. The documentation site
mirrors it at [docs.codecarbon.io/latest/how-to/examples/](https://docs.codecarbon.io/latest/how-to/examples/).

## Setup

Most examples need only CodeCarbon itself:

```bash
pip install codecarbon
```

Examples that train or run models need extra libraries (TensorFlow, PyTorch,
scikit-learn). Installing them all is a large download, so prefer installing
only what the example you want actually imports:

```bash
pip install -r examples/requirements-examples.txt
```

The public API used throughout is `EmissionsTracker`, `OfflineEmissionsTracker`,
`track_emissions` and `OutputMethod`.

## Start here

| Example | What it shows |
|---|---|
| [`mnist_context_manager.py`](mnist_context_manager.py) | The recommended entry point: `with EmissionsTracker() as tracker:` |
| [`mnist.py`](mnist.py) | Explicit `EmissionsTracker` object with `start()` and `stop()` |
| [`mnist_decorator.py`](mnist_decorator.py) | The `@track_emissions` decorator on a function |
| [`notebook.ipynb`](notebook.ipynb) | Tracking inside a Jupyter notebook |
| [`notebooks/codecarbon_workshop.ipynb`](notebooks/codecarbon_workshop.ipynb) | Full hands-on workshop covering the whole feature set |
| [`print_hardware.py`](print_hardware.py) | Dump the CPU, GPU and RAM CodeCarbon detected on this machine |

## Tracking parts of a run

| Example | What it shows |
|---|---|
| [`mnist_callback.py`](mnist_callback.py) | A Keras callback that records emissions after each epoch |
| [`task_inference.py`](task_inference.py) | `start_task()` / `stop_task()` to attribute emissions to named phases |
| [`task_loop_same_task.py`](task_loop_same_task.py) | Repeatedly measuring the same named task |
| [`mnist_grid_search.py`](mnist_grid_search.py) | Emissions across a hyperparameter grid search |
| [`mnist_random_search.py`](mnist_random_search.py) | Emissions across a random search |

## Models and inference

| Example | What it shows |
|---|---|
| [`mnist-sklearn.py`](mnist-sklearn.py) | scikit-learn training |
| [`mnist_inference.py`](mnist_inference.py) | Measuring inference rather than training |
| [`bert_inference.py`](bert_inference.py) | BERT inference with task-level tracking |
| [`transformers_smollm2.py`](transformers_smollm2.py) | Hugging Face Transformers with SmolLM2 |
| [`local_llms.ipynb`](local_llms.ipynb) | Comparing local LLM runs |
| [`ollama_local_api.py`](ollama_local_api.py) | Tracking calls to a local Ollama server |
| [`pytorch-multigpu-example.py`](pytorch-multigpu-example.py) | Multi-GPU PyTorch training |
| [`intel_npu.py`](intel_npu.py) | Inference on an Intel NPU |

## Sending results somewhere

| Example | What it shows |
|---|---|
| [`logging_to_file.py`](logging_to_file.py) | Writing the CodeCarbon log to a file |
| [`logging_to_file_exclusive_run.py`](logging_to_file_exclusive_run.py) | File logging for a long-running exclusive run |
| [`logging_to_google_cloud.py`](logging_to_google_cloud.py) | Google Cloud Logging output |
| [`logfire_metrics.py`](logfire_metrics.py) | Logfire metrics output |
| [`prometheus_call.py`](prometheus_call.py) | Exporting metrics to Prometheus |
| [`boamps_output.py`](boamps_output.py) | Writing output in [BoAmps](https://github.com/Boavizta/BoAmps) format |
| [`mnist-comet.py`](mnist-comet.py) | Pairing tracking with [Comet](https://www.comet.com) experiment tracking |
| [`api_call_demo.py`](api_call_demo.py) | Minimal example sending data to the CodeCarbon API |
| [`api_call_debug.py`](api_call_debug.py) | Same, with debug logging and a 20-second interval, for troubleshooting |

## Configuration and process patterns

| Example | What it shows |
|---|---|
| [`pue.py`](pue.py) | Applying a datacenter Power Usage Effectiveness multiplier |
| [`wue.py`](wue.py) | Applying a Water Usage Effectiveness factor |
| [`multithread.py`](multithread.py) | Several `OfflineEmissionsTracker` instances across threads |
| [`command_line_tool.py`](command_line_tool.py) | Wrapping an external binary run via `subprocess` (machine-level, not process-level) |
| [`full_cpu.py`](full_cpu.py) | Saturating the CPU to produce a clear measurement signal |

## Hardware debugging

Use these when the numbers look wrong and you need to see what CodeCarbon is
reading from your hardware.

| Example | What it shows |
|---|---|
| [`compare_cpu_load_and_RAPL.py`](compare_cpu_load_and_RAPL.py) | Compare the CPU-load estimate against RAPL ground truth |
| [`compare_cpu_load_and_RAPL.ipynb`](compare_cpu_load_and_RAPL.ipynb) | The same comparison as an annotated notebook with plots |
| [`emi_channels.py`](emi_channels.py) | Print every Windows Energy Meter Interface channel and the power it reports |
| [`rapl/`](rapl/) | RAPL domain inspection and DRAM-handling diagnostics |
| [`test_rapl_calculus.sh`](test_rapl_calculus.sh) | Shell script reading raw RAPL counters around a `full_cpu.py` run |

## Clusters

| Example | What it shows |
|---|---|
| [`slurm_rocm/`](slurm_rocm/) | SLURM batch scripts and AMD ROCm/`amdsmi` examples |

See also the [SLURM how-to guide](https://docs.codecarbon.io/latest/how-to/slurm/).

## Sample data

[`emissions.csv`](emissions.csv) is a sample output file. Use it to try the
local dashboard without running a workload first:

```bash
carbonboard --filepath="examples/emissions.csv" --port=8050
```
