# Troubleshooting

This page is organized by the message or symptom you actually see.

If something looks wrong, first turn on debug logging so you can see what
CodeCarbon is doing:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(log_level="debug")
```

or from the CLI:

```bash
codecarbon monitor --log-level debug
```

Then dump what CodeCarbon detected about your machine:

```bash
codecarbon detect
```

Please include the output of `codecarbon detect` in any bug report.

## Nothing was measured / emissions are zero

### "Another instance of codecarbon is already running. Exiting."

Concurrent trackers are allowed by default (`allow_multiple_runs=True`). Only
when you set `allow_multiple_runs=False` does CodeCarbon take a machine-wide
lock so that two trackers do not double-count the same hardware. With the lock
enabled, if a previous run crashed, a notebook cell was re-executed, or a
`codecarbon monitor` process is running in another terminal, the lock is still
held and the new tracker does nothing — `start()`, `start_task()`, `flush()`
and `stop()` all return immediately.

What to do:

- Set `allow_multiple_runs=True` (or the environment variable
  `CODECARBON_ALLOW_MULTIPLE_RUNS=True`) to go back to the default behaviour and
  skip the lock entirely. This is what CodeCarbon's own test suite does.
- Check for a leftover process and stop it (`ps aux | grep codecarbon`).
- The lock is a file named `.codecarbon.lock` in the system temporary
  directory — `/tmp/.codecarbon.lock` on Linux and macOS, and the equivalent of
  `%TEMP%\.codecarbon.lock` on Windows (CodeCarbon uses Python's
  `tempfile.gettempdir()`). If no CodeCarbon process is running, it is safe to
  delete it:

  ```bash
  rm /tmp/.codecarbon.lock
  ```

At debug level you will also see the related message
`Lock file /tmp/.codecarbon.lock already exists. This usually means another
instance of codecarbon is running.`

### The tracker ran but `emissions.csv` is empty or missing

The CSV row is written when the tracker stops or flushes. If `stop()` is never
reached — because your code raised, because the process was killed, or because
the notebook cell was interrupted — nothing is written.

- Use the context manager or the decorator so that stopping is guaranteed even
  on an exception:

  ```python
  with EmissionsTracker() as tracker:
      train_model()
  ```

- Call `tracker.flush()` inside a long-running loop if you want partial results
  written as you go.
- The file is written to `output_dir`, which defaults to `.` — the *current
  working directory of the process*, not the directory containing your script.
  If you cannot find `emissions.csv`, set `output_dir` explicitly to an
  absolute path.
- Very short runs can legitimately produce values that round to zero in the
  displayed precision. `measure_power_secs` defaults to 15 seconds in the Python
  API and 10 seconds for `codecarbon monitor` (which also uses an
  `api_call_interval` of 30 measures); a run
  shorter than one measurement interval has very little to report.

## The numbers look wrong

### "We saw that you have a ... but we don't know it. Please contact us." { #unknown-cpu-model }

Your CPU model was detected, but it is not listed in
`codecarbon/data/hardware/cpu_power.csv`, so CodeCarbon has no TDP for it. It
falls back to a default power figure per thread, which is an estimate, not a
measurement.

This warning literally asks you to contact the project, so please do — adding a
line to that CSV is a one-line contribution that improves accuracy for everyone
with the same chip. See the
[Contribution Guidelines](contributing.md), and include the exact CPU name from
`codecarbon detect`.

On Linux, enabling RAPL removes the need for the TDP table entirely, because
the energy is then measured rather than estimated. See
[Improve Measurement Accuracy with RAPL](enable-rapl.md).

### "We will use the default power consumption of ... W per thread"

This is the fallback that follows the warning above. CodeCarbon multiplies a
fixed default power per thread by your thread count to obtain an assumed TDP,
then scales it by CPU load.

Two independent approximations stack up here: the assumed TDP, and the
load-to-power model. Expect the result to be indicative rather than accurate,
and treat comparisons across different machines with caution. Comparisons
between two runs on the *same* machine remain meaningful, because the same
approximation applies to both.

See [Power Estimation](../explanation/power-estimation.md) for what the
estimation model does, and [Accuracy and
validation](../explanation/accuracy.md) for how the backends compare.

### "We were unable to detect your CPU using the `cpuinfo` package."

CodeCarbon could not identify the CPU at all, so it cannot even look up a TDP.
The same per-thread default is used. This happens most often in containers and
virtual machines that hide CPU model information, and on some ARM platforms.

If you know your hardware, the accurate route is to stop relying on detection:
enable RAPL on Linux, or supply your own power figures. If detection fails on a
platform where the model *is* visible, that is worth reporting as a bug — please
include the output of `codecarbon detect`.

### Emissions seem far too high or too low

Emissions are energy multiplied by the carbon intensity of your grid, and
energy includes a datacenter overhead factor. Check all three inputs before
concluding the measurement is wrong:

- **Carbon intensity.** Read the `country_name`, `country_iso_code`, `region`
  and `cloud_region` columns of your `emissions.csv` and confirm they describe
  where the machine really is. Online mode geolocates by IP,
  which is wrong for VPNs and some cloud regions. Use
  `OfflineEmissionsTracker(country_iso_code="FRA")` to pin it. A grid can
  legitimately differ by a factor of ten between countries, which alone
  explains most surprising comparisons.
- **PUE.** The `pue` column shows the multiplier that was applied; it defaults
  to 1. If you set it, everything scales by it.
- **Power.** Compare the `cpu_power`, `gpu_power` and `ram_power` columns
  against what you expect for your hardware. If `cpu_power` looks like a
  suspiciously round fraction of a TDP, you are on the estimation fallback
  described above rather than on a measurement.

The full column list is in [Output](../reference/output.md), and the
calculation is described in [Methodology](../explanation/methodology.md).

## Linux: RAPL

### "RAPL - Permission denied reading RAPL file ..." { #rapl-permission-denied }

Also seen as `RAPL - Permission denied listing ...`, `... scanning ... for RAPL
domains` or `... reading name file ...`. Since a kernel security fix the energy
counters under `/sys/class/powercap/` are root-readable only, so CodeCarbon
falls back to estimating from CPU load and TDP. The quick fix does not survive a
reboot:

```bash
sudo chmod -R a+r /sys/class/powercap/*
```

For the persistent udev rule and the security tradeoff, see [Improve Measurement
Accuracy with RAPL](enable-rapl.md).

### "RAPL - No package domains found, falling back to psys"

Only the platform domain is exposed, so readings cover the whole SoC rather than
the CPU package and will not line up with the CPU TDP. Expected on several
laptop platforms and some newer Intel generations; it is not an error. If no
domain can be selected you see `RAPL - No package or psys domains found, using
all available domains` instead. See [RAPL
Metrics](../explanation/rapl.md) for the domain hierarchy.

### "RAPL - psys domain detected but not used (rapl_prefer_psys=False)"

Both domains are available and CodeCarbon chose `package`, which is more
consistent with CPU TDP specifications. Pass `rapl_prefer_psys=True` to the
tracker for total platform power instead; expect the figure to rise.

### No RAPL at all: containers, VMs, WSL

`/sys/class/powercap/` is not exposed inside most containers, most virtual
machines, or under WSL, so CodeCarbon silently estimates. `codecarbon detect`
confirms which mode you are in. For Docker on bare metal, mount the path
read-only (`-v /sys/class/powercap:/sys/class/powercap:ro`); see [Docker and
Containerized
Environments](enable-rapl.md#docker-and-containerized-environments). Under a
hypervisor there is nothing to do from inside the guest — and on shared hardware
RAPL would report energy for the whole physical CPU rather than your share, so
the estimate answers a different question rather than being a degraded
measurement.

## macOS

On Apple Silicon, CodeCarbon does not use `powermetrics`. `psutil` is a hard
dependency of the package, and the backend selector picks CPU-load estimation
as soon as `psutil` is importable, before `powermetrics` is ever tried
([`resource_tracker.py:228-233`](https://github.com/mlco2/codecarbon/blob/master/codecarbon/core/resource_tracker.py#L228)).
Granting passwordless `sudo` for `powermetrics` will not change which backend is
used. See
[Which backend gets chosen](../explanation/methodology.md#which-backend-gets-chosen).

On Intel Macs, CodeCarbon uses Intel Power Gadget when it is installed, and
`powermetrics` when it is not. `powermetrics` requires root: CodeCarbon runs it
through `sudo` and first checks whether that `sudo` call would prompt for a
password. If a prompt is detected, CodeCarbon logs at debug level *"Not using
PowerMetrics, sudo password prompt detected"* and falls back to estimation,
since a library cannot answer an interactive prompt. To get measured values
there, grant passwordless `sudo` for `powermetrics` alone by adding a line like
this with `sudo visudo`:

```bash
username ALL = (root) NOPASSWD: /usr/bin/powermetrics
```

Run with `log_level="debug"` to confirm the check now passes.

### "Returncode while logging power values using Powermetrics"

`powermetrics` started but exited with a non-zero status. Run the same command
by hand to see the real error, check that the binary is present at
`/usr/bin/powermetrics`, and confirm the sudoers entry above is still in effect
after any OS upgrade.

## Windows

### "Returncode while logging power values using Intel Power Gadget"

Intel Power Gadget exited with a non-zero status, so no power values were read
from it. Intel has discontinued Intel Power Gadget, and it does not work on
recent CPU generations, so on a modern machine this is expected rather than
fixable.

CodeCarbon's supported path on Windows is the Energy Meter Interface (EMI)
exposed by the platform driver. To see what your machine actually exposes, run:

```bash
python examples/emi_channels.py
```

That script prints every EMI channel and the power each one reports, which is
the fastest way to tell whether Windows is publishing usable counters at all.
If it prints no channels, your platform does not expose EMI and CodeCarbon
falls back to estimation.

## GPU

### Nvidia

CodeCarbon reads Nvidia GPUs through `nvidia-ml-py` (NVML). If NVML cannot talk
to the driver, no GPU is registered and you will see `There is no GPU
available` — GPU energy is then simply absent from the total, rather than
estimated. Check that `nvidia-smi` works as the same user; if it does not,
the problem is the driver or the container's device passthrough, not CodeCarbon.

### AMD

AMD GPUs are read through `amdsmi`, which ships with ROCm rather than from
PyPI. Two distinct warnings tell you which half is missing:

- *"AMD GPU detected but amdsmi is not available. Please install amdsmi to get
  GPU metrics."* — the Python module could not be imported at all.
- *"AMD GPU detected but amdsmi is not properly configured."* — the module
  imported but failed to initialize. This is almost always a version mismatch
  between the Python `amdsmi` package and the installed ROCm, or an outdated
  driver.

For a working ROCm setup, including how `amdsmi` is made visible to the Python
environment on a cluster, see [Run on SLURM (ROCm/PyTorch)](slurm.md) and the
scripts in `examples/slurm_rocm/`.

### `CUDA_VISIBLE_DEVICES` / `ROCR_VISIBLE_DEVICES` and `gpu_ids`

If you set `CUDA_VISIBLE_DEVICES` or `ROCR_VISIBLE_DEVICES`, CodeCarbon
populates `gpu_ids` from it automatically, so it measures only the GPUs your
job can see. Passing `gpu_ids` yourself overrides that. If your reported GPU
energy covers more or fewer devices than you expected, check both — one of them
is winning over the other. See the note in
[Parameters](../reference/api.md).

## Cloud API and dashboard

If runs do not appear on the dashboard, the tracker is still measuring
correctly — only the upload is failing. Errors from the API client are logged,
so run with `log_level="debug"` and look for messages from `ApiClient`.

Common causes:

- The API key or project token is missing, expired, or belongs to another
  project. Re-run `codecarbon login` and `codecarbon config`.
- The API is unreachable from your network — a proxy or firewall blocking
  outbound HTTPS is typical on clusters and in CI.
- The run was too short to reach an upload. An upload happens every
  `api_call_interval` measurements, so a short run may end before sending
  anything.

To isolate the API from the rest of your program, run the dedicated example,
which does a tracked run with frequent API calls and verbose logging:

```bash
python examples/api_call_debug.py
```

Setup and configuration are covered in
[Use the Cloud API & Dashboard](cloud-api.md).

## Still stuck?

Ask on [Discord](https://discord.gg/GS9js2XkJR) or
[open an issue](https://github.com/mlco2/codecarbon/issues), including the
output of `codecarbon detect` and a debug-level log.
