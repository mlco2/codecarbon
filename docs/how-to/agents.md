# Track Carbon Emissions with LLMs and Agents

Running large language models (LLMs) and AI agents locally with open-source models lets you build intelligent applications without relying on cloud APIs. CodeCarbon measures the carbon impact of running these local models and agents, helping you understand the environmental cost of inference and reasoning tasks.

## Installation

```console
pip install codecarbon transformers torch
```

## Running Local Model Inference

Here's how to track the carbon emissions of running inference with a local language model:

```python
# mktestdocs: skip
from transformers import AutoTokenizer, AutoModelForCausalLM
from codecarbon import EmissionsTracker
import torch

# Load a lightweight open-source model
model_name = "HuggingFaceTB/SmolLM2-135M-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Move to GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Track inference emissions
with EmissionsTracker() as tracker:
    messages = [
        {"role": "user", "content": "What are the benefits of renewable energy?"}
    ]

    # Format input for the model
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to(device)

    # Generate response
    outputs = model.generate(inputs, max_new_tokens=100, temperature=0.7)
    response = tokenizer.decode(outputs[0])

print(f"Inference emissions: {tracker.final_emissions:.6f} kg CO2eq")
print(f"Model response: {response}")
```

## What Gets Logged

When you run the example above, CodeCarbon creates an `emissions.csv` file in your working directory with columns including:

- `timestamp`: when the measurement was taken
- `duration`: how long the inference took
- `emissions`: CO2 in kg
- `energy_kwh`: energy consumed in kilowatt-hours
- `cpu_power`: CPU power in watts
- `gpu_power`: GPU power in watts (if the model is running on GPU)

## Comparing Different Models

You can measure the carbon impact of different model sizes or model architectures:

```python
# mktestdocs: skip
models = [
    "HuggingFaceTB/SmolLM2-135M-Instruct",  # 135M parameters
    "HuggingFaceTB/SmolLM-360M-Instruct",   # 360M parameters
]

prompt = "Explain machine learning in one sentence."

for model_name in models:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

    with EmissionsTracker(save_file_path=f"emissions_{model_name.split('/')[-1]}.csv") as tracker:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(inputs["input_ids"], max_new_tokens=50)

    print(f"{model_name}: {tracker.final_emissions:.6f} kg CO2eq")
```

## Benefits of Local Models

- **Privacy**: No data leaves your machine
- **Cost**: No API charges or rate limits
- **Control**: Full visibility into model behavior and resource usage
- **Sustainability**: Run efficient open-source models aligned with your carbon budget

## Finding Lightweight Models

Popular lightweight open-source models for local inference:
- **SmolLM2 family** – 135M to 1.7B parameters, fast and efficient
- **Phi family** – Compact models with strong performance
- **Mistral** – Small but capable models
- **TinyLlama** – 1.1B parameter model, ideal for edge devices

Smaller models consume less energy while still providing useful inference capabilities.

## Comparing Model Efficiency

To understand the trade-offs between different models, batch sizes, and their carbon impact, see [Comparing Model Efficiency](../tutorials/comparing-model-efficiency.md). You can apply the same patterns to compare different open-source models running locally.

## Next Steps

- [Configure CodeCarbon](configuration.md) to customize tracking behavior
- [Send emissions data to the cloud](cloud-api.md) to visualize inference emissions across multiple runs
- Explore other frameworks in [HuggingFace Transformers](transformers.md) or [Diffusers](diffusers.md)
