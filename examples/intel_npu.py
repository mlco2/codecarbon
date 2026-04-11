"""

## Prerequisites

Install OpenVINO and PyTorch CPU versions :
uv pip install -U openvino
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv run examples/intel_npu.py

### Linux support for Intel® Neural Processing Unit (Intel® NPU)

Chaeck if drivers are installed and the NPU is available:
`sudo dmesg | grep vpu` should show something like this if the NPU is properly initialized:
[nnnnn] [drm] Initialized intel_vpu 1.0.0 for 0000:00:0b.0 on minor 0

Else, have a look to https://github.com/intel/linux-npu-driver/releases

### Windows support

You just need to install the Intel drivers.

"""

import os

import openvino as ov
import torch
from torchvision.models import ShuffleNet_V2_X1_0_Weights, shufflenet_v2_x1_0

from codecarbon import track_emissions

NUMBER_OF_IMAGES = 30


@track_emissions(
    measure_power_secs=5,
    save_to_file=False,
    log_level="debug",
)
def openvino_npu_task():
    print("openvino", ov.__version__)
    model = shufflenet_v2_x1_0(weights=ShuffleNet_V2_X1_0_Weights.DEFAULT)
    print("training before eval", model.training)
    model.eval()
    print("training after eval", model.training)
    # Create a dummy input tensor with the appropriate shape for the model (e.g., [10, 3, 224, 224] for image classification).
    example = torch.randn(NUMBER_OF_IMAGES, 3, 224, 224)
    ov_model = ov.convert_model(
        model, example_input=(example,), input=[NUMBER_OF_IMAGES, 3, 224, 224]
    )
    print("input partial shape", ov_model.input(0).partial_shape)
    for i, out in enumerate(ov_model.outputs):
        print("output", i, out.partial_shape)
    core = ov.Core()
    print("devices", core.available_devices)
    if "NPU" in core.available_devices:
        compiled = core.compile_model(ov_model, "NPU")
        print("compiled on", compiled.get_property("EXECUTION_DEVICES"))
        result = compiled({0: example.numpy()})
        print("result shape", result[compiled.output(0)].shape)
        # output_data = result[compiled.output(0)]
        # Classification outputs are flat vectors (e.g. [10, 1000]).
        # Render the top-3 scores as simple ASCII bars for terminal readability.
        output_data = next(iter(result.values()))
        # For classification output shaped like [batch, classes], show top-k per image.
        # If output is 1D, treat it as a single-image prediction.
        if output_data.ndim == 1:
            output_data = output_data.reshape(1, -1)

        for image_idx, image_scores in enumerate(output_data):
            top_k = min(3, image_scores.size)
            top_indices = image_scores.argsort()[-top_k:][::-1]
            top_values = image_scores[top_indices]
            max_score = float(top_values.max()) if top_values.size else 1.0
            scale = max_score if max_score > 0 else 1.0

            print(f"Top predictions for image {image_idx} (index: score | bar):")
            for idx, score in zip(top_indices, top_values):
                bar_len = int(40 * float(score) / scale)
                bar = "#" * max(0, bar_len)
                print(f"  {int(idx):4d}: {float(score): .6f} | {bar}")
    else:
        print("NPU unavailable")


# Display my process PID so you can check its power usage with `sudo dmesg | grep vpu` in another terminal.
print(f"Process PID: {os.getpid()}")
openvino_npu_task()
