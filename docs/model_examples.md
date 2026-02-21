# Model Comparisons {#model_examples}

The following table shows the different electricity consumption of
popular NLP and Computer visions models

  -----------------------------------------------------------------------
  Model             GPU               Training Time (H) Consumption (kWh)
  ----------------- ----------------- ----------------- -----------------
  BERT~fintetune~   4 V100            6                 3.1

  BERT~pretrain~    8 V100            36                37.3

  6B~Transf.~       256 A100          192               13 812.4

  Dense~121~        1 P40             0.3               0.02

  Dense~169~        1 P40             0.3               0.03

  Dense~201~        1 P40             0.4               0.04

  ViT~Tiny~         1 V100            19                1.7

  ViT~Small~        1 V100            19                2.2

  ViT~Base~         1 V100            21                4.7

  ViT~Large~        4 V100            90                93.3

  ViT~Huge~         4 V100            216               237.6
  -----------------------------------------------------------------------

  : Electricity consumption of AI cloud instance

## Impact of time of year and region

Carbon emissions that would be emitted from training BERT (language
modeling on 8 V100s for 36 hours) in different locations:

![Models emissions comparison](./_images/CO2_emitted_BERT.png){.align-center}

In this case study, time of year might not be relevant in most cases,
but localisation can have a great impact on carbon emissions.

Here, and in the graph below, emissions equivalent are estimated using
Microsoft Azure cloud tools. CodeCarbon has developed its own measuring
tools. The result could be different.

## Comparisons

Emissions for the 11 described models can be displayed as below:

![Models emissions comparison](./_images/model_emission_comparison.png){.align-center}

The black line represents the average emissions (across regions and time
of year). The light blue represents the first and fourth quartiles. On
the right side, equivalent sources of emissions are displayed as
comparison points (source : [US Environmental Protection
Agency](https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator)).
NB : presented on a log scale

## References

[Measuring the Carbon intensity of AI in Cloud
Instance](https://dl.acm.org/doi/10.1145/3531146.3533234)

Another source comparing models carbon intensity: [Energy and Policy
Considerations for Deep Learning in
NLP](https://arxiv.org/pdf/1906.02243.pdf)
