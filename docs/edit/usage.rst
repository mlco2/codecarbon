.. _usage:

Quickstart
==========
The CO2 tracking tool can be used along with any computing framework. It supports both ``online`` (with internet access) and
``offline`` (without internet access) modes. The tracker can be used in following ways:


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
   # GPU intensive training code
   emissions = tracker.stop()


Decorator
~~~~~~~~~
In case the training code base is wrapped in a function, users can use the decorator ``@track_emissions`` within the function to enable tracking
emissions of the training code.

.. code-block:: python

   from codecarbon import track_emissions
   # Results are saved to a `emissions.csv` file
   # in the same directory by default.
   @track_emissions
   def training_function():
       # training code goes here



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


Decorator
~~~~~~~~~
The ``track_emissions`` decorator in offline mode requires following two parameters:

- ``offline`` needs to be set to ``True``, which defaults to ``False`` for online mode.
- ``country_iso_code`` the 3-letter alphabet ISO Code of the country where the compute infrastructure is hosted

.. code-block:: python

   from codecarbon import track_emissions
   @track_emissions(offline=True, country_iso_code="CAN")
   def training_function():
       # training code goes here


The Carbon emissions will be saved to a ``emissions.csv`` file in the same directory. Please refer to the :ref:`complete API <parameters>` for
additional parameters and configuration options.


Configuration
=============

Codecarbon is structured so that you can configure it in a hierarchical manner: you can set *global* parameters in ``~/.codecarbon.config``, *local* parameters (with respect to the current working directory) in ``./.codecarbon.config``, *shell* parameters as environment variables  starting with ``CODECABON_`` and finally *script* parameters in the tracker's initialization as ``EmissionsTracker(param=value)``.

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
            save_to_file=true
            output_dir=/Users/victor/emissions
            co2_signal_api_token=script-overwrite


* environment variables

	.. code-block:: bash

	    export CODECARBON_GPU_IDS="0, 1"

* script:

	.. code-block:: python

	     EmissionsTracker(co2_signal_api_token="some-token")

Yields attributes:

.. code-block:: python

    {
        "measure_power_secs": 10,
        "save_to_file": True,
        "emissions_endpoint": "localhost:7777",
        "output_dir": "/Users/victor/emissions",
        "co2_signal_api_token": "some-token",
        "gpu_ids": [0, 1],
    }

.. |ConfigParser| replace:: ``ConfigParser``
.. _ConfigParser: https://docs.python.org/3/library/configparser.html#module-configparser

.. note:: If you're wondering about the configuration files' syntax, be aware that under the hood ``codecarbon`` uses |ConfigParser|_ which relies on the `INI syntax <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_
