.. CO2 Tracker documentation master file, created by
   sphinx-quickstart on Thu Jun  4 11:09:10 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CO2 Tracker's documentation!
=======================================

Installation
------------
We recommend using Python 3.6 or above. The CO2 tracking tool can be installed using pip::

   pip install co2_tracker


Quickstart
----------

The CO2 tracking tool can be used along with any deep learning framework. It supports both online and offline modes of operation. A full example can be found  :doc:`here. <../quickstart>`
The tracker can be used in the following two ways

Explicit Object
~~~~~~~~~~~~~~~
.. code-block:: python

   tracker = CO2Tracker()
   tracker.start()
   # GPU intensive training code
   emissions = tracker.stop()


Decorator
~~~~~~~~~

.. code-block:: python

   # Results are saved to a default.emissions file
   # in the same directory.
   @track_co2
   def training_loop():
       # training code goes here


Offline Usage
~~~~~~~~~~~~~
An offline version is available to support environments without internet access. The usage is identical, however, a ``country`` parameter is required like so.

.. code-block:: python

   tracker = OfflineCO2Tracker(country="Canada")
   tracker.start()
   # GPU intensive training code
   tracker.stop()

   @track_co2(offline=True, country="Canada")
   def training_loop():
       # training code goes here


The CO2 emissions will be saved to a ``.emissions`` file in the same directory. Please refer to the full API documentation for additional configuration options.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   source/co2_tracker




