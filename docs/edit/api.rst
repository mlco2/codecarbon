.. _api:

CodeCarbon API
==============


CodeCarbon API
~~~~~~~~~~~~~~

.. warning::
    This mode use the CodeCarbon API to upload the timeseries of your emissions on a central server. All data will be public!

Before using it, you need an experiment_id, to get one, run:

.. code-block:: console

    codecarbon init

It will create an experiment_id for the default project and save it to ``codecarbon.config``

Then you can tell CodeCarbon to monitor your machine:

.. code-block:: console

    codecarbon monitor

Or use the API in your code:

.. code-block:: python

    from codecarbon import track_emissions

    @track_emissions(save_to_api=True)
    def train_model():
        # GPU intensive training code  goes here

    if __name__ =="__main__":
        train_model()

More options could be specified in ``@track_emissions`` or in ``.codecarbon.config``

The `CodeCarbon dashboard <https://dashboard.codecarbon.io/>`_ use `CodeCarbon API <https://api.codecarbon.io/>`_ to get the data

The API do not have a nice web interface to create your own organization and project, you have to use `OpenAPI interface <https://api.codecarbon.io/docs>`_ for that.

And so on for your team, project and experiment.

You then have to set you experiment id in CodeCarbon, with two options:

In the code:

.. code-block:: python

    from codecarbon import track_emissions

    @track_emissions(
        measure_power_secs=30,
        api_call_interval=4,
        experiment_id="your experiment id",
        save_to_api=True,
    )
    def train_model():
        ...

Or in the config file `.codecarbon.config`:

.. code-block:: ini

    [codecarbon]
    experiment_id = your experiment id
    save_to_api = true
