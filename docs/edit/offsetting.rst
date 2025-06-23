Carbon Offsetting with OneClickImpact
====================================

CodeCarbon integrates with OneClickImpact to provide automatic carbon offsetting capabilities. This allows you to not only track your carbon emissions but also automatically offset them through verified capture carbon projects.

Features
--------

- **Automatic Offsetting**: Offset emissions automatically as they are generated
- **Threshold-based Offsetting**: Set minimum emission thresholds before triggering offsets
- **Manual Control**: Disable auto-offset and trigger offsets manually
- **Carbon Capture**: Offsets are performed through OneClickImpact's carbon capture projects
- **Sandbox Mode**: Test integration safely without real offsetting

Setup
-----

1. Install the offset dependency:

.. code-block:: bash

   pip install codecarbon[offset]

2. Get a OneClickImpact API key from `OneClickImpact <https://1clickimpact.com>`_

3. Configure your tracker with OneClickImpact parameters

Basic Usage
-----------

Using EmissionsTracker
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from codecarbon import EmissionsTracker

   tracker = EmissionsTracker(
       project_name="my_project",
       offset_api_key="your_api_key_here",
       offset_environment="production",  # or "sandbox" for testing
       offset_threshold=0.5,  # Offset when reaching 0.5 kg CO2 (minimum is 0.5 kg or 1 lb)
       auto_offset=True,
   )

   tracker.start()
   # Your code here
   emissions = tracker.stop()

Using the Decorator
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from codecarbon import track_emissions

   @track_emissions(
       project_name="my_function",
       offset_api_key="your_api_key_here",
       offset_environment="production",
       auto_offset=True,
   )
   def my_carbon_intensive_function():
       # Your code here
       pass

Configuration Parameters
-------------------------

.. list-table:: OneClickImpact Parameters
   :widths: 25 75
   :header-rows: 1

   * - Parameter
     - Description
   * - offset_api_key
     - Your OneClickImpact API key (required for offsetting)
   * - offset_environment
     - Environment: "production" for real offsetting, "sandbox" for testing (default: "production")
   * - offset_threshold
     - Minimum emissions in kg CO2 before triggering offset (minimum: 0.5, default: 0.5)
   * - auto_offset
     - Whether to automatically offset emissions (default: True)

Advanced Usage
--------------

Manual Offset Control
~~~~~~~~~~~~~~~~~~~~~

You can disable automatic offsetting and control it manually:

.. code-block:: python

   tracker = EmissionsTracker(
       project_name="manual_control",
       offset_api_key="your_api_key_here",
       auto_offset=False,  # Disable automatic offsetting
   )

   tracker.start()
   # Your code here
   emissions = tracker.stop()

   # Access the OneClickImpact handler for manual control
   for handler in tracker._output_handlers:
       if hasattr(handler, 'manual_offset'):
           # Check accumulated emissions
           accumulated = handler.get_accumulated_emissions()
           print(f"Accumulated: {accumulated:.6f} kg CO2")
           
           # Manually trigger offset
           success = handler.manual_offset()
           if success:
               print("Offset successful!")

Threshold-based Offsetting
~~~~~~~~~~~~~~~~~~~~~~~~~~

Set a minimum threshold to accumulate emissions before offsetting:

.. code-block:: python

   tracker = EmissionsTracker(
       project_name="threshold_example",
       offset_api_key="your_api_key_here",
       offset_threshold=2,  # Only offset after 2 kg CO2 accumulated
       auto_offset=True,
   )

Configuration File
------------------

You can also configure OneClickImpact parameters in your `.codecarbon.config` file:

.. code-block:: ini

   [codecarbon]
   offset_api_key = your_api_key_here
   offset_environment = production
   offset_threshold = 1
   auto_offset = true

How It Works
------------

1. **Emission Tracking**: CodeCarbon tracks your code's carbon emissions as usual
2. **Accumulation**: Emissions are accumulated until the threshold is reached
3. **Conversion**: Emissions are converted from kg CO2 to pounds (lbs) for the OneClickImpact API
4. **Capture Carbon**: OneClickImpact's `capture_carbon()` method is called to offset the emissions
5. **Verification**: The offset is logged and emissions counter is reset

Sandbox vs Production
-------------------------

- **Sandbox Environment**: Use for testing integration without real offsetting
- **Production Environment**: Use for actual carbon offsetting through verified projects

Example with Real Usage
-----------------------

.. code-block:: python

   from codecarbon import track_emissions

   @track_emissions(
       project_name="ml_training",
       offset_api_key="your_real_api_key",
       offset_environment="production",
       offset_threshold=0.5,  # Offset every 0.5 kg CO2
   )
   def train_ml_model():
       # Your ML training code
       model = create_model()
       model.fit(training_data)
       return model

   # This will automatically track emissions and offset them when threshold is reached
   model = train_ml_model()

Cost Considerations
-------------------

- Offsetting costs vary based on the amount of CO2 and chosen projects
- Consider setting appropriate thresholds for your use case
- Monitor your offset costs through OneClickImpact's platform
- Use sandbox mode for testing to avoid unnecessary costs

Troubleshooting
---------------

**ImportError: No module named 'makeimpact'**

Install the offset dependencies:

.. code-block:: bash

   pip install codecarbon[offset]

**Failed to initialize OneClickImpact SDK**

- Verify your API key is correct
- Check your internet connection
- Ensure the OneClickImpact service is available

**No offsetting happening**

- Check that `auto_offset=True`
- Verify emissions exceed your `offset_threshold`
- Look for error messages in the logs
- Ensure you're using a valid API key

**Unexpected offset amounts**

- Remember that offsets happen when thresholds are reached
- Check accumulated emissions with `get_accumulated_emissions()`
- Verify your threshold settings

For more information, visit the `OneClickImpact documentation <https://docs.1clickimpact.com>`_.
