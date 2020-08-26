.. _usage:

Quickstart
==========
The CO2 tracking tool can be used along with any deep learning framework. It supports both ``online`` (with internet access) and
``offline`` (without internet access) modes. The tracker can be used in following ways.


Online Mode
-----------
When the environment has internet access ``CO2Tracker`` object or vanilla ``track_co2`` decorator can be used, which has parameter
``offline`` defaulted to ``False``.

Explicit Object
~~~~~~~~~~~~~~~
In case of absence of a single entry and stop point to the training code base, users can instantiate a ``CO2Tracker`` object and
pass it as a param to function calls to start and stop the emissions tracking of the compute section.

.. code-block:: python

   from co2_tracker import CO2Tracker
   tracker = CO2Tracker()
   tracker.start()
   # GPU intensive training code
   emissions = tracker.stop()


Decorator
~~~~~~~~~
In case the training code base is wrapped in a function, users can use the decorator ``@track_co2`` on the function to enable tracking
emissions of the training code.

.. code-block:: python

   from co2_tracker import track_co2
   # Results are saved to a `emissions.csv` file
   # in the same directory by default.
   @track_co2
   def training_function():
       # training code goes here



Offline Mode
------------
An offline version is available to support restricted environments without internet access. The internal computations remain unchanged, however,
a ``country_iso_code`` parameter is required to fetch Carbon Intensity details of the regional electricity used.

Explicit Object
~~~~~~~~~~~~~~~
Developers can use ``OfflineCO2Tracker`` object to track emissions in absence of internet access as follows.

.. code-block:: python

   from co2_tracker import OfflineCO2Tracker
   tracker = OfflineCO2Tracker(country_iso_code="CAN")
   tracker.start()
   # GPU intensive training code
   tracker.stop()


Decorator
~~~~~~~~~
``track_co2`` decorator in offline mode requires following two parameters:

- ``offline`` set to ``True``, which defaults to ``False`` to support online mode.
- ``country_iso_code`` as the 3-letter alphabet ISO Code of the country where the compute infrastructure is hosted, for example - CAN for Canada.

.. code-block:: python

   from co2_tracker import track_co2
   @track_co2(offline=True, country_iso_code="CAN")
   def training_function():
       # training code goes here


The CO2 emissions will be saved to a ``emissions.csv`` file in the same directory. Please refer to the full API documentation for additional configuration options.

