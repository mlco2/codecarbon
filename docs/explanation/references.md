# References

The literature and data sources behind CodeCarbon's
[methodology](methodology.md). The [accuracy](accuracy.md) and
[alternatives](alternatives.md) pages cite this list rather than repeating it.

## Foundational work

Strubell, E., Ganesh, A., & McCallum, A. (2019). *Energy and Policy
Considerations for Deep Learning in NLP*. Proceedings of the 57th Annual
Meeting of the Association for Computational Linguistics (ACL 2019).
<https://arxiv.org/abs/1906.02243>

Lacoste, A., Luccioni, A., Schmidt, V., & Dandres, T. (2019). *Quantifying
the Carbon Emissions of Machine Learning*. arXiv preprint arXiv:1910.09700.
<https://arxiv.org/abs/1910.09700>

Lottick, K., Susai, S., Friedler, S. A., & Wilson, J. P. (2019). *Energy
Usage Reports: Environmental awareness as part of algorithmic
accountability*. Workshop on Tackling Climate Change with Machine Learning,
NeurIPS 2019. <https://arxiv.org/abs/1911.08354>

Henderson, P., Hu, J., Romoff, J., Brunskill, E., Jurafsky, D., & Pineau, J.
(2020). *Towards the Systematic Reporting of the Energy and Carbon Footprints
of Machine Learning*. Journal of Machine Learning Research, 21(248), 1–43.
<https://jmlr.org/papers/v21/20-312.html>

Patterson, D., Gonzalez, J., Le, Q., Liang, C., Munguia, L.-M., Rothchild, D.,
So, D., Texier, M., & Dean, J. (2021). *Carbon Emissions and Large Neural
Network Training*. arXiv preprint arXiv:2104.10350.
<https://arxiv.org/abs/2104.10350>

Luccioni, A. S., Viguier, S., & Ligozat, A.-L. (2022). *Estimating the Carbon
Footprint of BLOOM, a 176B Parameter Language Model*. arXiv preprint
arXiv:2211.02001. <https://arxiv.org/abs/2211.02001>

## Hardware measurement

Khan, K. N., Hirki, M., Niemi, T., Nurminen, J. K., & Ou, Z. (2018). *RAPL in
Action: Experiences in Using RAPL for Power Measurements*. ACM Transactions on
Modeling and Performance Evaluation of Computing Systems, 3(2), Article 9,
1–26. <https://dl.acm.org/doi/10.1145/3177754>

Weaver, V. M. *Reading RAPL energy measurements from Linux*.
<https://web.eece.maine.edu/~vweaver/projects/rapl/>

Microsoft. *Energy Meter Interface (EMI) driver documentation*.
<https://learn.microsoft.com/en-us/windows-hardware/drivers/powermeter/energy-meter-interface>

Chih, M. *Read CPU power with RAPL*.
<https://blog.chih.me/read-cpu-power-with-RAPL.html>

## Carbon intensity data sources

Our World in Data. *Carbon intensity of electricity generation*.
<https://ourworldindata.org/grapher/carbon-intensity-electricity> — the source
of the per-country intensities in `global_energy_mix.json`.

International Energy Agency (2019). *Global Energy & CO2 Status Report*.
<https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions> —
the source of the 475 gCO₂eq/kWh world average.

Electricity Maps. *Carbon intensity API*.
<https://portal.electricitymaps.com/docs/getting-started> — optional live
carbon intensity, used when an API token is configured.

Google Cloud. *Carbon free energy for Google Cloud regions*.
<https://cloud.google.com/sustainability/region-carbon> — the source of the GCP
rows in `impact.csv`.

Responsible Problem Solving. *Energy Usage — conversion to CO2*.
<https://github.com/responsibleproblemsolving/energy-usage#conversion-to-co2> —
the per-fuel intensities for fossil sources.

World Nuclear Association. *Comparison of lifecycle greenhouse gas emissions of
various electricity generation sources*.
<https://www.world-nuclear.org/uploadedFiles/org/WNA/Publications/Working_Group_Reports/comparison_of_lifecycle.pdf>
— the per-fuel intensities for low-carbon sources.

## Equivalence factors

The car, television and household equivalences shown in the dashboard come from
the US EPA; see [equivalences](equivalences.md) for the exact figures and their
derivations.

## Citing CodeCarbon

Use
[CITATION.cff](https://github.com/mlco2/codecarbon/blob/master/CITATION.cff),
or the "Cite this repository" button on the
[GitHub repository](https://github.com/mlco2/codecarbon).
