# CO2 Tracker


## Setup
Create a virtual environment using `conda` or `virtualenv.` 

```
conda env create --name co2_tracker_env
conda activate co2_tracker_env
pip install -r requirements.txt  # We need this for now as co2_tracker_utils is not published to PyPI
```

`co2_tracker` will now be installed to the local environment
```python
from co2_tracker import CO2Tracker
tracker = CO2Tracker()
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```

Or use the decorator

```python
from co2_tracker import track_co2

@track_co2
def training_loop():
   pass
```

For an example application, we use TensorFlow 2.0 on MNIST. 

```
pip install tensorflow
```

Run the examples in `examples/` like so

```
python examples/mnist.py
python examples/mnist_decorator.py
```

## Tests

Make sure `tox` is available

```
pip install tox
```

Run tests by simply entering tox in the terminal when in the root package directory.

```
tox
```

## Generate Documentation
Install [`sphinx.`](https://www.sphinx-doc.org/en/master/usage/installation.html) On MacOS,  
```
brew install sphinx-doc
cd docs
make html
```

