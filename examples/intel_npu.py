"""

## Linux support for Intel® Neural Processing Unit (Intel® NPU)

See https://github.com/intel/linux-npu-driver/releases

`sudo dmesg | grep vpu` should show something like this if the NPU is properly initialized:
[nnnnn] [drm] Initialized intel_vpu 1.0.0 for 0000:00:0b.0 on minor 0



uv pip install -U openvino
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv run examples/intel_npu.py



"""

import openvino as ov
import torch
from torchvision.models import ShuffleNet_V2_X1_0_Weights, shufflenet_v2_x1_0

# load PyTorch model into memory
model = shufflenet_v2_x1_0(weights=ShuffleNet_V2_X1_0_Weights.DEFAULT)
model.eval()

# convert the model into OpenVINO model
example = torch.randn(1, 3, 224, 224)
ov_model = ov.convert_model(model, example_input=(example,))

# compile the model for CPU device
core = ov.Core()
available_devices = core.available_devices
print(available_devices)
if "NPU" not in available_devices:
    raise RuntimeError(
        "NPU device is not available. Please check your OpenVINO installation."
    )
compiled_model = core.compile_model(ov_model, "NPU")

# infer the model on random data
output = compiled_model({0: example.numpy()})
print(len(output))
