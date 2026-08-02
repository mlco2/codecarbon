# CodeCarbon Examples

The directory [examples/](https://github.com/mlco2/codecarbon/tree/master/examples) contains practical examples demonstrating how to use CodeCarbon to track carbon emissions from your computing tasks. The examples below are organized by use case rather than alphabetically.

## Quick Start Examples

| Example | Type | Description |
|---------|------|-------------|
| [print_hardware.py](https://github.com/mlco2/codecarbon/blob/master/examples/print_hardware.py) | Python Script | Detect and display available hardware (CPU, GPU, RAM) on your system |
| [command_line_tool.py](https://github.com/mlco2/codecarbon/blob/master/examples/command_line_tool.py) | Python Script | Track emissions of external command-line tools executed via subprocess |

## Tracking Methods

| Example | Type | Description |
|---------|------|-------------|
| [mnist_decorator.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist_decorator.py) | Python Script | Track emissions using the `@track_emissions` decorator on functions |
| [mnist_context_manager.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist_context_manager.py) | Python Script | Track emissions using `EmissionsTracker` as a context manager (with statement) |
| [mnist_callback.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist_callback.py) | Python Script | Track emissions using Keras/TensorFlow callbacks during model training |
| [api_call_demo.py](https://github.com/mlco2/codecarbon/blob/master/examples/api_call_demo.py) | Python Script | Track emissions and send data to the CodeCarbon API with `@track_emissions` |

## Basic Model Training

| Example | Type | Description |
|---------|------|-------------|
| [mnist.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist.py) | Python Script | Train a simple neural network on MNIST dataset with TensorFlow |
| [mnist-sklearn.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist-sklearn.py) | Python Script | Train a scikit-learn model on MNIST and track emissions |
| [pytorch-multigpu-example.py](https://github.com/mlco2/codecarbon/blob/master/examples/pytorch-multigpu-example.py) | Python Script | PyTorch CNN training on MNIST with multi-GPU support |

## Hyperparameter Search

| Example | Type | Description |
|---------|------|-------------|
| [mnist_grid_search.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist_grid_search.py) | Python Script | Grid search hyperparameter optimization with emission tracking |
| [mnist_random_search.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist_random_search.py) | Python Script | Random search hyperparameter optimization with emission tracking |

## ML Model Inference

| Example | Type | Description |
|---------|------|-------------|
| [bert_inference.py](https://github.com/mlco2/codecarbon/blob/master/examples/bert_inference.py) | Python Script | BERT language model inference with task-level tracking |
| [task_inference.py](https://github.com/mlco2/codecarbon/blob/master/examples/task_inference.py) | Python Script | Track emissions for different inference tasks (load dataset, build model, predict) |
| [task_loop_same_task.py](https://github.com/mlco2/codecarbon/blob/master/examples/task_loop_same_task.py) | Python Script | Track emissions running the same task multiple times |
| [transformers_smollm2.py](https://github.com/mlco2/codecarbon/blob/master/examples/transformers_smollm2.py) | Python Script | Small language model (SmolLM2) inference from Hugging Face |
| [ollama_local_api.py](https://github.com/mlco2/codecarbon/blob/master/examples/ollama_local_api.py) | Python Script | Track emissions of local LLM API calls using Ollama |

## Hardware-Specific Examples

| Example | Type | Description |
|---------|------|-------------|
| [intel_npu.py](https://github.com/mlco2/codecarbon/blob/master/examples/intel_npu.py) | Python Script | Intel Neural Processing Unit (NPU) support for model inference |
| [full_cpu.py](https://github.com/mlco2/codecarbon/blob/master/examples/full_cpu.py) | Python Script | Demonstrate full CPU utilization and emission tracking |

## Parallel & Concurrent Processing

| Example | Type | Description |
|---------|------|-------------|
| [multithread.py](https://github.com/mlco2/codecarbon/blob/master/examples/multithread.py) | Python Script | Track emissions from multithreaded workloads |
| [compare_cpu_load_and_RAPL.py](https://github.com/mlco2/codecarbon/blob/master/examples/compare_cpu_load_and_RAPL.py) | Python Script | Compare RAPL power measurement vs CPU load estimation in parallel workloads |

## Logging & Output Integration

| Example | Type | Description |
|---------|------|-------------|
| [boamps_output.py](https://github.com/mlco2/codecarbon/blob/master/examples/boamps_output.py) | Python Script | Write the output in [BoAmps](https://github.com/Boavizta/BoAmps) format. |
| [logging_to_file.py](https://github.com/mlco2/codecarbon/blob/master/examples/logging_to_file.py) | Python Script | Save emissions data to a local CSV file |
| [logging_to_file_exclusive_run.py](https://github.com/mlco2/codecarbon/blob/master/examples/logging_to_file_exclusive_run.py) | Python Script | Long-running process with exclusive file logging |
| [logging_to_google_cloud.py](https://github.com/mlco2/codecarbon/blob/master/examples/logging_to_google_cloud.py) | Python Script | Send emissions data to Google Cloud Logging |
| [logfire_metrics.py](https://github.com/mlco2/codecarbon/blob/master/examples/logfire_metrics.py) | Python Script | Integrate CodeCarbon with Logfire metrics platform |
| [prometheus_call.py](https://github.com/mlco2/codecarbon/blob/master/examples/prometheus_call.py) | Python Script | Export emissions metrics to Prometheus |
| [mnist-comet.py](https://github.com/mlco2/codecarbon/blob/master/examples/mnist-comet.py) | Python Script | Integrate emission tracking with Comet.ml experiment tracking |

## Metrics & Analysis

| Example | Type | Description |
|---------|------|-------------|
| [pue.py](https://github.com/mlco2/codecarbon/blob/master/examples/pue.py) | Python Script | Calculate Power Usage Effectiveness (PUE) with CodeCarbon |
| [wue.py](https://github.com/mlco2/codecarbon/blob/master/examples/wue.py) | Python Script | Calculate Water Usage Effectiveness (WUE) of your computing |

## Interactive Notebooks

| Example | Type | Description |
|---------|------|-------------|
| [notebook.ipynb](https://github.com/mlco2/codecarbon/blob/master/examples/notebook.ipynb) | Jupyter Notebook | Basic CodeCarbon usage in Jupyter environment |
| [compare_cpu_load_and_RAPL.ipynb](https://github.com/mlco2/codecarbon/blob/master/examples/compare_cpu_load_and_RAPL.ipynb) | Jupyter Notebook | Compare different power measurement methods (RAPL vs CPU load) |
| [local_llms.ipynb](https://github.com/mlco2/codecarbon/blob/master/examples/local_llms.ipynb) | Jupyter Notebook | Track emissions of local LLM inference |

## Setup & Configuration

| Item | Description |
|------|-------------|
| [requirements-examples.txt](https://github.com/mlco2/codecarbon/blob/master/examples/requirements-examples.txt) | Python dependencies for running the examples |
| [rapl/](https://github.com/mlco2/codecarbon/blob/master/examples/rapl/) | Setup instructions for RAPL power measurement support |
| [slurm_rocm/](https://github.com/mlco2/codecarbon/blob/master/examples/slurm_rocm/) | Configuration for SLURM job scheduler with ROCm GPU support |
| [notebooks/](https://github.com/mlco2/codecarbon/blob/master/examples/notebooks/) | Additional Jupyter notebooks |

## Running the Examples

### Prerequisites
```bash
# Install CodeCarbon
pip install codecarbon

# Install example dependencies
# WARNING: it will download huge pacakge. We recommand you to install only the minimum you need for the example you want to run.
pip install -r examples/requirements-examples.txt
```

### Run a Python Example
```bash
# Using uv (recommended)
uv run examples/print_hardware.py

# Or with Python directly
python examples/print_hardware.py
```

### Run a Jupyter Notebook
```bash
jupyter notebook examples/notebook.ipynb
```

Or just open it in VS Code.

## Common Patterns

### Track with Decorator
```python
from codecarbon import track_emissions

@track_emissions(project_name="my_project")
def my_function():
    # Your code here
    pass
```

### Track with Context Manager
```python
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    # Your code here
    pass
```

### Track Specific Tasks
```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()
tracker.start_task("data_loading")
# Load data...
tracker.stop_task()

tracker.start_task("training")
# Train model...
tracker.stop_task()
tracker.stop()
```
