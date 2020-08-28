# Emissions Tracker
Emissions Tracker is a Python package for tracking the carbon emissions produced by various kinds of computer programs, from straightforward algorithms to deep neural networks. 
￼
Sasha Luccioni, PhD
AI/ML Researcher - Mila & Université de Montréal, 2020 National Geographic Explorer, IVADO Fellow

Who viewed your profile
949
Views of your post
2,883
Access exclusive tools & insights
 Try Premium Free for 1 Month
 Saved items
Recent
￼
AI for GOOD
AI Works!
Artificial Intelligence & Robotics
Artificial Intelligence
Artificial Intelligence Applications
GroupsSee all Groups
￼
AI for GOOD
AI Works!
Artificial Intelligence & Robotics
￼Show more Show more Groups
Events
￼
￼
10th International Advance Computing Conference
Followed HashtagsSee all Followed Hashtags
Discover more
￼
Start a post
￼
Photo
￼
Video
￼
Document
Write article
￼
Sort by:
Top
Feed Updates
Feed post
Kristine Gloria, Ph.D. celebrates this
￼
￼
Grace Abuhamad
 • 2nd

By taking into account your computing infrastructure, location, usage and running time, Emissions Tracker can provide an estimate of how much CO2 you produced, and give you some comparisons with common modes of transporation to give you an order of magnitude. 


## Setup
Create a virtual environment using `conda` or `virtualenv.` 

```
conda env create --name codecarbon_env
conda activate codecarbon_env
pip install . 
```

`codecarbon` will now be installed to the local environment

#### Online mode (for setups with internet access)

```python
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```

Or use the decorator

```python
from codecarbon import track_emissions

@track_emissions
def training_loop():
   pass
```
#### Offline mode (for setups without internet access)

The offline tracker can be used as follows:
```python
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(country="Canada")
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```

or 

```python
from codecarbon import track_emissions

@track_emissions(offline=True, country="Canada")
def training_loop():
   pass
```

## Quickstart

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
