CO2 Tracker API
====================

CO2 Tracker
--------------------------------

.. autoclass:: co2_tracker.CO2Tracker
   :members:
   :undoc-members:
   :inherited-members:

.. code-block:: python

   tracker = CO2Tracker(project_name="foo", output_dir="emissions/")
   tracker.start()
   # GPU intensive training code
   emissions = tracker.stop()



Offline CO2 Tracker
--------------------------------

.. autoclass:: co2_tracker.OfflineCO2Tracker
   :members:
   :undoc-members:
   :inherited-members:

.. code-block:: python

   tracker = OfflineCO2Tracker(country="Canada")
   tracker.start()
   # GPU intensive training code
   tracker.stop()

Decorator
--------------------------------
.. autofunction:: co2_tracker.track_co2

.. code-block:: python

   @track_co2(project_name="foo", output_dir="emissions/")
   def training_loop():
       # training code goes here
