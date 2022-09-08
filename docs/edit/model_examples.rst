.. _model_examples:

Model Comparisons
=================

The following table shows the different electricity consumption of popular NLP and Computer visions models

.. list-table:: Electricity consumtion of AI cloud instance
   :widths: 20 20 20 20  
   :align: center
   :header-rows: 1

   * - Model
     - GPU
     - Training Time (H)
     - Consumption (kWh)
   * - BERT\ :sub:`fintetune`\
     - 4 V100
     - 6
     - 3.1
   * - BERT\ :sub:`pretrain`\
     - 8 V100
     - 36
     - 37.3
   * - 6B\ :sub:`Transf.`\
     - 256 A100
     - 192
     - 13 812.4
   * - Dense\ :sub:`121`\
     - 1 P40
     - 0.3
     - 0.02
   * - Dense\ :sub:`169`\
     - 1 P40
     - 0.3
     - 0.03
   * - Dense\ :sub:`201`\
     - 1 P40
     - 0.4
     - 0.04     
   * - ViT\ :sub:`Tiny`\
     - 1 V100
     - 19
     - 1.7
   * - ViT\ :sub:`Small`\
     - 1 V100
     - 19
     - 2.2
   * - ViT\ :sub:`Base`\
     - 1 V100
     - 21
     - 4.7
   * - ViT\ :sub:`Large`\
     - 4 V100
     - 90
     - 93.3
   * - ViT\ :sub:`Huge`\
     - 4 V100
     - 216
     - 237.6

Impact of time of year and regions
---------------------------------------

Carbon emissions that would be emitted from training BERT (language modeling on 8 V100s for 36 hours) :


.. image:: ./images/CO2_emitted_BERT.png
            :align: center
            :alt: Models emissions comparison
            :height: 430px
            :width: 633px

Here and in the graph below emissions equivalent are estimated using Microsoft Azure cloud tools. 
Code Carbon had developped its own mesuring tools. The result could be different.

Comparisons
---------------------

Emissions for the 11 described models can be desplayed as below:

.. image:: ./images/model_emission_comparison.png
            :align: center
            :alt: Models emissions comparison
            :height: 430px
            :width: 633px

The black line represent the average emissions (across regions and time of year). 
The light blue represent the firts and fourth quartiles.
On the right side, equivalent sources of emissions are displayed as comparating points (source : `US Environmental Protection Agency <https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator>`_)
NB : presented on a log scale



References
----------
`Mesuring the Carbon intensity of AI in Cloud Instance <https://facctconference.org/static/pdfs_2022/facct22-145.pdf>`_

Other source comparing models carbon intensity : 
`Energy and Policy Considerations for Deep Learning in NLP <https://arxiv.org/pdf/1906.02243.pdf>`_
