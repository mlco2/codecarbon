.. _usage:

Quickstart
==========
The CO2 tracking tool can be used along with any computing framework. It supports both ``online`` (with internet access) and
``offline`` (without internet access) modes. The tracker can be used in the following ways:


Online Mode
-----------
When the environment has internet access, the ``EmissionsTracker`` object or the ``track_emissions`` decorator can be used, which has
``offline`` parameter set to ``False`` by default.

Explicit Object
~~~~~~~~~~~~~~~
In the case of absence of a single entry and stop point for the training code base, users can instantiate a ``EmissionsTracker`` object and
pass it as a parameter to function calls to start and stop the emissions tracking of the compute section.

.. code-block:: python

   from codecarbon import EmissionsTracker
   tracker = EmissionsTracker()
   tracker.start()
   # Compute intensive code goes here
   tracker.stop()

This mode is recommended when using a Jupyter Notebook. You call ``tracker.start()`` at the beginning of the Notebook, and call ``tracker.stop()`` in the last cell.

Context manager
~~~~~~~~~~~~~~~~
The ``Emissions tracker`` also works as a context manager.

.. code-block:: python

    from codecarbon import EmissionsTracker

    with EmissionsTracker() as tracker:
        # Compute intensive training code goes here

This mode is recommended when you want to monitor a specific block of code.

Decorator
~~~~~~~~~
In case the training code base is wrapped in a function, users can use the decorator ``@track_emissions`` within the function to enable tracking
emissions of the training code.

.. code-block:: python

   from codecarbon import track_emissions

   @track_emissions
   def training_loop():
       # Compute intensive training code goes here

This mode is recommended if you have a training function.

.. note::
    This will write a csv file named emissions.csv in the current directory

CodeCarbon API (BETA)
~~~~~~~~~~~~~~~~~~~~~~~~
*(This feature is currently in BETA stage, meaning all features are not available)*

.. warning::
    This mode use the CodeCarbon API to upload the timeseries of your emissions on a central server. All data will be public!

Before using it, you need an experiment_id, to get one, run:

.. code-block:: console

    codecarbon init

It will create a experiment_id on the default project and save it to ``codecarbon.config``

Then you could tell CodeCarbon to monitor your machine :

.. code-block:: console

    codecarbon monitor

Or use the API in your code

.. code-block:: python

    from codecarbon import track_emissions

    @track_emissions(save_to_api=True)
    def train_model():
        # GPU intensive training code  goes here
    if __name__ =="__main__":
        train_model()

More options could be specified in ``@track_emissions`` or in ``.codecarbon.config``

Offline Mode
------------
An offline version is available to support restricted environments without internet access. The internal computations remain unchanged; however,
a ``country_iso_code`` parameter, which corresponds to the 3-letter alphabet ISO Code of the country where the compute infrastructure is hosted, is required to fetch Carbon Intensity details of the regional electricity used. A complete list of country ISO codes can be found on `Wikipedia <https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes>`_.

Explicit Object
~~~~~~~~~~~~~~~
Developers can use the ``OfflineEmissionsTracker`` object to track emissions as follows:

.. code-block:: python

   from codecarbon import OfflineEmissionsTracker
   tracker = OfflineEmissionsTracker(country_iso_code="CAN")
   tracker.start()
   # GPU intensive training code
   tracker.stop()

Context manager
~~~~~~~~~~~~~~~~
The ``OfflineEmissionsTracker`` also works as a context manager

.. code-block:: python

    from codecarbon import OfflineEmissionsTracker

    with OfflineEmissionsTracker() as tracker:
    # GPU intensive training code  goes here


Decorator
~~~~~~~~~
The ``track_emissions`` decorator in offline mode requires following two parameters:

- ``offline`` needs to be set to ``True``, which defaults to ``False`` for online mode.
- ``country_iso_code`` the 3-letter alphabet ISO Code of the country where the compute infrastructure is hosted

.. code-block:: python

   from codecarbon import track_emissions
   @track_emissions(offline=True, country_iso_code="CAN")
   def training_loop():
       # training code goes here
       pass


The Carbon emissions will be saved to a ``emissions.csv`` file in the same directory. Please refer to the :ref:`complete API <parameters>` for
additional parameters and configuration options.


Configuration
=============

Configuration priority
----------------------

CodeCarbon is structured so that you can configure it in a hierarchical manner:
    * *global* parameters in your home folder ``~/.codecarbon.config``
    * *local* parameters (with respect to the current working directory) in ``./.codecarbon.config``
    * *environment variables* parameters starting with ``CODECARBON_``
    * *script* parameters in the tracker's initialization as ``EmissionsTracker(param=value)``

.. warning:: Configuration files **must** be named ``.codecarbon.config`` and start with a section header ``[codecarbon]`` as the first line in the file.

For instance:

* ``~/.codecarbon.config``

    .. code-block:: bash

            [codecarbon]
            measure_power_secs=10
            save_to_file=local-overwrite
            emissions_endpoint=localhost:7777


* ``./.codecarbon.config``

	.. code-block:: bash

            [codecarbon]
            save_to_file = true
            output_dir = /Users/victor/emissions
            co2_signal_api_token=script-overwrite
            experiment_id = 235b1da5-aaaa-aaaa-aaaa-893681599d2c
            log_level = DEBUG
            tracking_mode = process

* environment variables

	.. code-block:: bash

	    export CODECARBON_GPU_IDS="0, 1"

* script:

	.. code-block:: python

	     EmissionsTracker(
            api_call_interval=4,
            save_to_api=True,
            co2_signal_api_token="some-token")

Yields attributes:

.. code-block:: python

    {
        "measure_power_secs": 10,
        "save_to_file": True,
        "api_call_interval": 4,
        "save_to_api": True,
        "experiment_id": "235b1da5-aaaa-aaaa-aaaa-893681599d2c",
        "log_level": "DEBUG",
        "tracking_mode": "process",
        "emissions_endpoint": "localhost:7777",
        "output_dir": "/Users/victor/emissions",
        "co2_signal_api_token": "some-token",
        "gpu_ids": [0, 1],
    }

.. |ConfigParser| replace:: ``ConfigParser``
.. _ConfigParser: https://docs.python.org/3/library/configparser.html#module-configparser

.. note:: If you're wondering about the configuration files' syntax, be aware that under the hood ``codecarbon`` uses |ConfigParser|_ which relies on the `INI syntax <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_.

Access internet through proxy server
------------------------------------

If you need a proxy to access internet, which is needed to call a Web API, like `Codecarbon API <https://api.codecarbon.io/docs>`_, you have to set environment variable ``HTTPS_PROXY``, or *HTTP_PROXY* if calling an ``http://`` enpoint.

You could do it in your shell:

.. code-block:: shell

    export HTTPS_PROXY="http://0.0.0.0:0000"

Or in your Python code:

.. code-block:: python

    import os
    os.environ["HTTPS_PROXY"] = "http://0.0.0.0:0000"

For more information, please read the `requests library proxy documentation <https://requests.readthedocs.io/en/latest/user/advanced/#proxies>`_
