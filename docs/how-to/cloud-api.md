# Use the Cloud API & Dashboard

This guide shows how to send your emissions data to the CodeCarbon cloud platform, where you can visualize results and collaborate with your team on a shared dashboard.

!!! warning "API Mode"

    API mode uploads your emissions data to CodeCarbon's central server. Thanks to [CleverCloud](https://www.clever.cloud/), usage is free within reasonable limits.

![CodeCarbon architecture](https://github.com/mlco2/codecarbon/raw/master/carbonserver/Images/code_carbon_archi.png){.align-center width="700px" height="400px"}

## Prerequisites

First, we'll create an account and authenticate your local environment:

1. Create an account on the [CodeCarbon dashboard](https://dashboard.codecarbon.io/)
2. Run `codecarbon login` from your terminal to authenticate

The login command will create a default project and save your credentials to `.codecarbon.config`.

## Send Emissions from Your Code

With your account set up, you're ready to start sending emissions data. Use the `save_to_api=True` parameter to upload tracking data:

``` python
from codecarbon import track_emissions

@track_emissions(save_to_api=True)
def train_model():
    # GPU intensive training code  goes here

if __name__ =="__main__":
    train_model()
```

The decorator will automatically send your emissions data to the dashboard. You can also specify additional options in `@track_emissions()` or in `.codecarbon.config`.

## Create Projects & Experiments

By default, `codecarbon login` creates a default experiment in your first project. If you want to organize runs by experiment, you can specify an `experiment_id` explicitly. Set the experiment ID in two ways:

**Option 1: In your code**

``` python
from codecarbon import track_emissions

@track_emissions(
    experiment_id="your experiment id",
    save_to_api=True,
)
def train_model():
    ...
```

**Option 2: In `.codecarbon.config`**

``` ini
[codecarbon]
experiment_id = your experiment id
save_to_api = true
```

## View Your Results

Once your runs complete, visit the [CodeCarbon dashboard](https://dashboard.codecarbon.io/) to see your results. For more visualization options, see the [visualization guide](visualize.md).
