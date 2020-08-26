.. _model_examples:

Model Comparisons
=================

Following table illustrates Carbon Footprint from compute of training popular models across different hardware.

.. list-table:: Carbon Footprint and Compute Cost of Training of Popular Models
   :widths: 16 16 16 16 16 20
   :header-rows: 1

   * - Model
     - Hardware
     - Power (W)
     - Training Time (hr)
     - CO₂eq (lbs)
     - Cloud Compute Cost ($)
   * - Transformer\ :sub:`base`\
     - P100x8
     - 1,415.78
     - 12
     - 26
     - $41 - $410
   * - Transformer\ :sub:`big`\
     - P100x8
     - 1,515.43
     - 84
     - 192
     - $289 - $981
   * - ELMo
     - P100x3
     - 517.66
     - 336
     - 262
     - $433 - $1,472
   * - BERT\ :sub:`base`\
     - V100x64
     - 12,041.51
     - 79
     - 1,438
     - $3751 - $12,571
   * - NAS
     - P100x8
     - 1,515.43
     - 274,120
     - 626,155
     - $942,973–$3,201,722



Exemplary Equivalents
---------------------

Following are some examples from daily life depicting amounts of Carbon Emitted.

.. list-table:: Carbon Footprint Across Routine Activities
   :widths: 50 50
   :header-rows: 1

   * - Consumption
     - CO₂eq (lbs)
   * - Air travel, 1 passenger, NY↔SF
     - 1,984
   * - Avg Human Life, 1 year
     - 11,023
   * - Avg American Life, 1 year
     - 36,156
   * - Avg Car Including Fuel, 1 lifetime
     - 126,000



References
----------
`Energy and Policy Considerations for Deep Learning in NLP <https://arxiv.org/pdf/1906.02243.pdf>`_
