.. _faq:

Frequently Asked Questions
===========================

* **How accurate are your estimations?**
	It is hard to quantify the entirety of computing emissions, because there are many factors in play, notably the life-cycle emissions of computing infrastructure. We therefore only focus on the direct emissions produced by running the actual code, but recognize that there is much work to be done to improve this estimation.

* **What are the sources of your energy carbon intensity data?**
	We use the following sources:

		For cloud computing:

		- Google publish carbon intensity of electricity for `Google Cloud Platform <https://cloud.google.com/sustainability/region-carbon?hl=fr>`_.

		- Unfortunately, Amazon has made a habit of keeping information about its carbon footprint out of public view. Although it released its global carbon footprint, it does not publish datacenter carbon footprints.

		- Microsoft has a Sustainability Calculator that helps enterprises analyze the carbon emissions of their IT infrastructure. But does not publish datacenter carbon intensity.


		For private infra:

		- When available we use data from `ourworld in data <https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=table>`_

		- if not available we use the electricity mix of the country find on `globalpetrolprices.com <https://www.globalpetrolprices.com/energy_mix.php>`_ that we multiply by the carbon intensity of the source of electricity (`that you can find here <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/carbon_intensity_per_source.json>`_)

		- if we have neither we default to a world average of 475 gCO2.eq/KWh from `IEA <https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions>`_.


* **How do I offset my emissions?**
	There are many offsetting schemes, and it is hard to recommend any single one. For one-shot offsetting, the `Gold Standard <https://www.goldstandard.org/>`_ is often used, and has many offsetting projects to choose from at different prices. There are often local initiatives as well, so try researching what exists in your region/country. For a recurring offset, `Project Wren <https://projectwren.com/>`_  lets you estimate your monthly carbon emissions and offset them via a monthly subscription. Keep in mind that offsetting is a good choice, but *reducing your emissions* should be the priority.


* **How can I help?**
	If you find a functionality missing in the CodeCarbon repo, please `open an issue <https://github.com/mlco2/codecarbon/issues>`_ so that you (and others!) can help add it. We did our best to cover all use cases and options, but we count on the open source community to help make the package an even greater success.


