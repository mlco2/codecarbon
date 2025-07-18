# Getting Started

## Setup

The following examples use Keras from TensorFlow 2.0. The dependencies can be installed as follows

```bash
pip install -r examples/requirements-examples.txt
```

## Examples
* [mnist.py](mnist.py): Usage using explicit `CO2Tracker` objects.
* [mnist_decorator.py](mnist_decorator.py): Using the `@track_co2` decorator.
* [mnist_callback.py](mnist_callback.py): Using Keras callbacks to save emissions after each epoch.
* [mnist-comet.py](mnist-comet.py): Using `CO2Tracker` with [`Comet`](https://www.comet.ml/site) for automatic experiment and emissions tracking.
* [api_call_demo.py](api_call_demo.py): Simplest demo to send computer emissions to CodeCarbon API.
* [api_call_debug.py](api_call_debug.py): Script to send computer emissions to CodeCarbon API. Made for debugging: debug log and send data every 20 seconds.
* And many more in the [examples](../examples) folder.
