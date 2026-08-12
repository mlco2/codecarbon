# CodeCarbon and the alternatives

Several tools measure or estimate the energy and carbon footprint of computing.
They overlap, but they were built for different jobs, and for some of the
questions below another tool is the better answer. This page tries to say so
plainly.

For the CodeCarbon versus EcoLogits question specifically — local hardware
versus remote GenAI APIs — see [When to use
CodeCarbon](when-to-use.md). The two are complementary rather than competing.

## At a glance

| Tool | Type | Language | Licence | Power source | Distinguishing capability |
|---|---|---|---|---|---|
| **CodeCarbon** | Library + CLI + hosted dashboard | Python | MIT | RAPL, NVML, amdsmi, macOS `powermetrics`, Windows EMI; TDP × load estimate as fallback | Per-task attribution, offline mode, several output backends |
| [ML CO2 Impact](https://mlco2.github.io/impact/) | Web calculator | — (web) | MIT | None — you enter hardware, hours and region | Estimate *before* you run; same `mlco2` GitHub organisation as CodeCarbon |
| [carbontracker](https://github.com/lfwa/carbontracker) | Library | Python | MIT | RAPL, NVML | Predicts a run's total footprint from its first epochs |
| [eco2AI](https://github.com/sb-ai-lab/Eco2AI) | Library | Python | Apache-2.0 | RAPL, NVML | Its own regional emission-intensity dataset |
| [experiment-impact-tracker](https://github.com/Breakend/experiment-impact-tracker) | Library | Python | MIT | RAPL, NVML | The original tool in this space; widely cited |
| [Zeus](https://github.com/ml-energy/zeus) | Library | Python | Apache-2.0 | NVML, RAPL | Energy/time trade-off optimisation, not only reporting |
| [Scaphandre](https://github.com/hubblo-org/scaphandre) | Agent / exporter | Rust | Apache-2.0 | RAPL | Host- and container-level metering, Prometheus-native |
| Cloud provider tools | Vendor console | — | proprietary | Provider-internal | Whole-account totals at billing granularity |

A note on `experiment-impact-tracker`: its GitHub repository is archived, with no
commits since January 2024. It remains worth knowing about, because many people
find the paper first and then look for the tool. If that is you, CodeCarbon,
carbontracker and eco2AI all cover the same ground and are receiving updates.

The table deliberately has no per-hardware yes/no columns. Almost every tool
answers "yes, if the counters are readable", so a grid of qualified yeses carries
no information. It also has no maintenance column, for the reason above: the
facts belong in prose with dates attached.

## Which one should you use?

### "I want to know the cost before I run it"

Use **ML CO2 Impact** or **carbontracker**. This is not what CodeCarbon does.

ML CO2 Impact is a web form: you pick a GPU, a region and a number of hours, and
it gives you an estimate plus a LaTeX snippet for your paper. Nothing to install,
nothing to instrument.

carbontracker measures the first epochs of a training run and extrapolates to the
full schedule, which lets you decide whether to continue before you have spent
the compute. If "should I run this at all" is your question, that is the right
shape of tool.

CodeCarbon reports what a run actually consumed, during and after the fact.

### "I want to attribute emissions to a specific function or training phase"

Use **CodeCarbon**. `tracker.start_task("name")` and `tracker.stop_task()` split
a single process into separately reported segments, so you can compare
preprocessing against training against inference inside one script. See
`examples/task_inference.py` and `examples/task_loop_same_task.py`.

### "I want to reduce energy use, not just report it"

Look at **Zeus** first. It comes from a systems-research angle and is built
around finding a good point on the energy/time trade-off curve — batch size,
power limit, GPU frequency — rather than around producing a footprint report.
CodeCarbon will tell you what a configuration costs; it will not search for a
better one.

### "I want to monitor a fleet, not a script"

**Scaphandre** is likely the better fit. It is an agent, not a library: it meters
whole hosts and containers without any change to the applications running on
them, and it exports to Prometheus natively. If your goal is a
datacenter-or-cluster dashboard and you are not instrumenting individual jobs,
start there.

CodeCarbon can do fleet work, but it approaches it from the other direction — it
starts inside the process and scales outward. If you want per-job attribution
*and* fleet aggregation, it has:

- a [Prometheus output](../how-to/logging.md) (`examples/prometheus_call.py`);
- a [Linux service deployment mode](../how-to/linux-service.md) that monitors a
  whole machine without instrumenting code;
- an [Ansible playbook](../how-to/ansible.md) for rolling that out;
- a hosted API and dashboard that aggregates across machines and projects.

### "I'm on SLURM or an HPC cluster"

CodeCarbon has a dedicated [SLURM guide](../how-to/slurm.md) covering multi-node
runs, plus ROCm and PyTorch examples under `examples/slurm_rocm/`. Most of the
alternatives leave the multi-node aggregation problem to you.

### "I need the total for my AWS or GCP account"

Use the provider's own tool: the AWS Customer Carbon Footprint Tool, Google Cloud
Carbon Footprint, or the Azure Emissions Impact Dashboard. They have access to
data no external library can see — actual facility PUE, the provider's own
energy contracts — and they cover your whole account, including services no
Python library can instrument.

They will not answer "what did *this training run* cost", because they report at
billing-account granularity with monthly latency. The two are complementary: the
provider console for reporting obligations, CodeCarbon for attributing a number
to a specific experiment.

### "I need something I can cite"

carbontracker, eco2AI and experiment-impact-tracker each have an accompanying
academic paper, and so does the methodology behind CodeCarbon. CodeCarbon also
has a Zenodo DOI: use the **Cite this repository** button in the GitHub sidebar,
or the BibTeX entry in the repository README. See also the
[Methodology](methodology.md) page. If a reviewer asks how accurate the numbers
are, [Accuracy and validation](accuracy.md) is the page to point at — including
its list of known gaps.

### "I'm not on Linux"

CodeCarbon reads `powermetrics` on macOS (Intel and Apple Silicon) and the Energy
Meter Interface on Windows 11, falling back to the TDP estimate elsewhere. Most
of the alternatives are Linux-first and rely on RAPL. If you are on a Mac or a
Windows machine, check platform support carefully whichever tool you pick — and
read the [accuracy page](accuracy.md), because a fallback estimate on any of
these tools is an estimate.

## What CodeCarbon is actually good at

Summarised, since the sections above are organised around other tools:

- **Breadth of measurement backends** with a documented fallback order — RAPL,
  NVML, amdsmi, `powermetrics`, Windows EMI, then TDP-based estimation. See
  [CPU metrics priority](methodology.md#which-backend-gets-chosen).
- **Task-level attribution** within a single process.
- **Offline mode** (`OfflineEmissionsTracker`) for air-gapped machines, with no
  no calls to the CodeCarbon API.
- **Output flexibility** — CSV, HTTP endpoint, logger, Prometheus, Logfire,
  BOAMPS, and the hosted API.
- **A hosted dashboard**, if you do not want to build the aggregation layer
  yourself.
- **A CLI**, so you can measure a process without writing any Python.

## Where CodeCarbon is the wrong choice

- You want a footprint estimate for a run you have not done yet → ML CO2 Impact,
  or carbontracker's prediction mode.
- You want to *optimise* energy use rather than report it → Zeus.
- You want host-level metering with no application changes and a Prometheus
  dashboard → Scaphandre.
- You are measuring calls to a hosted LLM API rather than local compute →
  [EcoLogits](when-to-use.md).
- You need an auditable total for a cloud account → the provider's own tool.

## Corrections welcome

Comparison pages go stale, and one that is wrong about another project is worse
than no page at all. If something here misrepresents a tool you work on, please
[open an issue](https://github.com/mlco2/codecarbon/issues) and it will be
fixed.

<!--
Every cell in the table above was checked against each project's own repository
(licence, language, latest release, archive status) on 2026-08-12.
Re-check at each minor release.
-->
