# Track your model's CO2 emissions

```python
import co2_tracker as co2
co2.track()

import torch

...

if __name__ == "__main__":
  main()
```

`co2_tracker` fits nicely with `comet_ml`:

```python
from comet_ml import Experiment

import torch
import torch.nn as nn

...

experiment = Experiment(track_co2=True) # This is the default value, turn off co2 measurements by setting to False

...
```
