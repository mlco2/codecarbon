"""
This example demonstrates how to use the CodeCarbon library to track the carbon emissions of a transformer model.

We will use the model from https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct

It's a small language model that fit on small GPU.
- 360M model took 1 GB on disk, less than 2 GB in VRAM.
- 1.7B model took 3.4 GB on disk, 7 GB in VRAM.

To run this example, you need to install the following dependencies:
    pip install transformers[torch]


@misc{allal2024SmolLM2,
      title={SmolLM2 - with great data, comes great performance},
      author={Loubna Ben Allal and Anton Lozhkov and Elie Bakouch and Gabriel Martín Blázquez and Lewis Tunstall and Agustín Piqueres and Andres Marafioti and Cyril Zakka and Leandro von Werra and Thomas Wolf},
      year={2024},
}

"""

import pynvml
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from codecarbon import EmissionsTracker

model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"


def print_gpu_usage(gpu_id):
    print(
        f">>>> GPU memoy: {pynvml.nvmlDeviceGetMemoryInfo(gpu_device).used / 1024**3:.2f} GB on {gpu_mem} GB"
    )
    print(
        f">>>> GPU usage: Load {pynvml.nvmlDeviceGetUtilizationRates(gpu_device).gpu} %, memory {pynvml.nvmlDeviceGetUtilizationRates(gpu_device).memory} %"
    )


if __name__ == "__main__":
    # Initialize the tracker
    tracker = EmissionsTracker()
    # Start tracking
    tracker.start()

    if torch.cuda.is_available():
        print("Using GPU")
        device = "cuda:0"
        gpu_device = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(gpu_device).total / 1024**3
        print_gpu_usage(gpu_device)
    else:
        print("Using CPU")
        device = "cpu"
        gpu_device = None

    # Load pre-trained model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Generate text
    generated_text = []
    for _ in range(10):
        input_text = "CodeCarbon is a library that "
        input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)
        model.to(device)
        output = model.generate(
            input_ids, max_length=100, num_return_sequences=3, do_sample=True
        )
        generated_text.append(tokenizer.batch_decode(output, skip_special_tokens=True))
        if gpu_device:
            print_gpu_usage(gpu_device)

    # Stop tracking
    tracker.stop()

    print("=" * 30)
    print(generated_text[-1])
    print("=" * 30)
    print(tracker.final_emissions_data)
