# Emissions Tracker
While computing currently represents roughly 0.5% of the world’s energy consumption, that percentage is projected to grow beyond 2% in the coming years, which will entail a significant rise in global CO2 emissions if not done properly. Given this increase, it is important to quantify and track the extent and origin of this energy usage, and to minimize the emissions incurred as much as possible.

For this purpose, we created **Emissions Tracker**, a Python package for tracking the carbon emissions produced by various kinds of computer programs, from straightforward algorithms to deep neural networks. 

By taking into account your computing infrastructure, location, usage and running time, Emissions Tracker can provide an estimate of how much CO<sub>2</sub> you produced, and give you some comparisons with common modes of transporation to give you an order of magnitude. 

Our hope is that this package will be used widely for estimating the carbon footprint of computing, and for establishing best practices with regards to the disclosure and reduction of this footprint.

Follow the steps below to set up the package and don't hesitate to open an issue if you need help!


## Setup
Create a virtual environment using `conda` for easier management of dependencies and packages. 
For installing conda, follow the instructions on the [official conda website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

```
conda create --name codecarbon python=3.6
conda activate codecarbon
pip install . 
```

`codecarbon` will now be installed in your the local environment

#### Online mode 
This is the most straightforward usage of the package, which is possible if you have access to the Internet, which is necessary to gather information regarding your geographical location.

```python
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```
You can also use the decorator:

```python
from codecarbon import track_emissions

@track_emissions
def training_loop():
   pass
```
#### Offline mode 
This mode can be used in setups without internet access, but requires a manual specification of your country code.
A complete list of country ISO codes can be found on [Wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes).

The offline tracker can be used as follows:
```python
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(country_iso_code="CAN")
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```

or by using the decorator:

```python
from codecarbon import track_emissions

@track_emissions(offline=True, country_iso_code="CAN")
def training_loop():
   pass
```

## Quickstart

As a simple illustration of using the package, we use a built-in example using TensorFlow for digit classification on the [MNIST dataset](http://yann.lecun.com/exdb/mnist/): 

First, install Tensorflow  2.0:

```
pip install tensorflow
```

Then, run the examples in the `examples/` folder:

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
Install [`sphinx`](https://www.sphinx-doc.org/en/master/usage/installation.html#installation-from-pypi) using pip. 
```
pip install -U sphinx
cd docs/edit
make docs
```

## Visualization Tool
* Sample data file is in `examples/emissions.csv`
* Run with the following command
```
python codecarbon/viz/carbonboard.py --filepath="examples/emissions.csv"
```
