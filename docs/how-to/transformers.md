# Track Carbon Emissions with HuggingFace Transformers

HuggingFace Transformers is the standard library for building and fine-tuning state-of-the-art NLP models. CodeCarbon integrates seamlessly with Transformers to measure the carbon impact of fine-tuning, inference, and other model operations.

## Installation

```console
pip install codecarbon transformers torch datasets
```

## Fine-tuning a Model

Here's how to track the carbon emissions when fine-tuning a HuggingFace model:

```python
# mktestdocs: skip
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
from codecarbon import EmissionsTracker

# Load a pre-trained model and tokenizer
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Load and prepare dataset
dataset = load_dataset("imdb")
def preprocess(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length")
dataset = dataset.map(preprocess, batched=True)

# Track fine-tuning emissions
with EmissionsTracker() as tracker:
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir="./results",
            num_train_epochs=3,
            per_device_train_batch_size=8,
        ),
        train_dataset=dataset["train"],
    )
    trainer.train()

print(f"Fine-tuning emissions: {tracker.final_emissions:.6f} kg CO2eq")
```

## What Gets Logged

When you run the example above, CodeCarbon creates an `emissions.csv` file in your working directory with columns including:

- `timestamp`: when the measurement was taken
- `duration`: how long the fine-tuning took
- `emissions`: CO2 in kg
- `energy_kwh`: energy consumed in kilowatt-hours
- `cpu_power`: CPU power in watts
- `gpu_power`: GPU power in watts (if applicable)

## Tracking Inference

You can also measure the carbon cost of running inference:

```python
# mktestdocs: skip
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    predictions = model.generate(input_ids, max_length=50)

print(f"Inference emissions: {tracker.final_emissions:.6f} kg CO2eq")
```

## Comparing Fine-tuning Approaches

To understand the trade-offs between different training configurations and their carbon impact, see [Comparing Model Efficiency](../tutorials/comparing-model-efficiency.md). You can apply the same patterns to compare Transformers models with different learning rates, batch sizes, or architectures.

## Next Steps

- [Configure CodeCarbon](configuration.md) to customize tracking behavior
- [Send emissions data to the cloud](cloud-api.md) to visualize across multiple fine-tuning runs
- Explore other frameworks in [Diffusers](diffusers.md) or [local model agents](agents.md)
