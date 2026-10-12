# Improve Measurement Accuracy with RAPL

RAPL (Running Average Power Limit) is a hardware feature on modern Intel and AMD processors that provides direct energy measurements through CPU counters. Enabling RAPL access gives CodeCarbon significantly more accurate CPU power measurements compared to software-based estimation.

## How RAPL Improves Accuracy

Without RAPL, CodeCarbon estimates CPU power based on hardware specifications and CPU load. With RAPL enabled, CodeCarbon reads actual energy consumption directly from the processor's energy counters, providing:

- ✅ **Direct hardware measurements** — Read CPU energy directly from RAPL counters
- ✅ **Higher precision** — Microjoule-level accuracy instead of estimates
- ✅ **Multi-domain support** — Measure package, core, uncore, DRAM, and GPU separately
- ✅ **Real-time data** — No delay or aggregation artifacts

## Prerequisites

- Linux system with RAPL-capable CPU (Intel Skylake or newer, AMD Ryzen, EPYC, etc.)
- Linux kernel 5.8+ (for AMD CPU support)
- `sudo` access to configure permissions
- CodeCarbon installed

## Check RAPL Availability

First, verify that your CPU supports RAPL:

```bash
ls /sys/class/powercap/intel-rapl*
```

If the command returns directories (e.g., `intel-rapl:0`, `intel-rapl:1`), your system has RAPL support.

## Setup Steps

### Step 1: Understand the Security Issue

Since [CVE-2020-8694](https://www.cve.org/CVERecord?id=CVE-2020-8694), the Linux kernel
restricts RAPL counters to root. The reason is the
[PLATYPUS attack](https://platypusattack.com/): power consumption is a side channel, and
`energy_uj` exposes it to software without needing an oscilloscope.

**What an attacker actually needs.** The threat is a process running *on the same machine*
as the victim, under an account allowed to read the counters. Remote attackers, and local
accounts outside the group you grant, gain nothing. What such a process can do, in
increasing order of difficulty:

| Capability | Requirements |
|---|---|
| Infer coarse activity: when a workload starts, roughly how busy it is, a covert channel between processes | Sampling the counter. Immediate. |
| Break KASLR (defeats a kernel exploit mitigation, does not by itself leak data) | ~20 seconds of sampling. |
| Recover a cryptographic key (AES-NI, RSA) | The victim must repeat the *same* operation with the *same* key tens of thousands of times while the attacker averages traces — 26 to 277 hours in the published results. The SGX variants also required privileged single-stepping (SGX-Step), not just counter access. |

So the intuition that key recovery needs a victim doing the same encryption with the same
key, over and over, for a very long time is correct: it is not a realistic threat against a
general-purpose workload. The cheap and realistic gains are **activity inference** and
**KASLR defeat as one link in an exploit chain**.

**How this guide limits the exposure:**

- **Access goes to a dedicated group**, not to all users, so an untrusted local account
  gains nothing.
- **Only `energy_uj` is exposed.** Power limits and other powercap attributes stay
  root-only, and nothing becomes writable — no risk of an attacker throttling or
  overheating the machine through this interface.

Judge it accordingly: on a single-tenant server or a personal workstation, granting a
service account read access to an energy counter is a minor change. On a machine where
untrusted code runs under other local accounts — shared build servers, multi-tenant hosts,
CI runners executing third-party jobs — keep the group tight, and prefer running CodeCarbon
under its own service user rather than making the counters world-readable.

### Step 2: Temporary Access (Testing)

To quickly check that RAPL works at all, without permanent changes:

```bash
sudo chmod a+r /sys/class/powercap/*/energy_uj
```

**Permissions are lost at next reboot**, so this is only a throwaway test — and it grants
access to every local user. Move on to step 3 for a real setup.

### Step 3: Permanent Access (Recommended)

For permanent access that survives reboots, add a `udev` rule. The rule fires every time a
powercap device appears, so it covers all RAPL domains (`package`, `core`, `dram`, `psys`,
MMIO) without listing them one by one, and it works on any distribution using `systemd`.

**Step 3a: Create a Dedicated Group**

```bash
sudo groupadd codecarbon
sudo usermod -a -G codecarbon $USER
```

Use the account that will run CodeCarbon — if it runs as a service, add that service user
instead of `$USER`.

**Step 3b: Create the Rule**

```bash
sudo tee /etc/udev/rules.d/99-codecarbon-rapl.rules <<'EOF'
SUBSYSTEM=="powercap", ACTION=="add", TEST=="energy_uj", \
  RUN+="/bin/chgrp codecarbon /sys%p/energy_uj", \
  RUN+="/bin/chmod 0440 /sys%p/energy_uj"
EOF
```

`%p` expands to the device path, so each RAPL domain is handled by its own event.
`TEST=="energy_uj"` skips devices that do not expose the counter. Only that one file
changes: mode `0440` means root and the `codecarbon` group can read it, nobody else, and
it stays read-only.

**Step 3c: Apply It Without Rebooting**

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=powercap --action=add
```

**Step 3d: Check the Result**

```bash
ls -l /sys/class/powercap/*/energy_uj
```

Each file should show `-r--r----- root codecarbon`. Log out and back in for your group
membership to take effect:

```bash
logout
# Then log back in
```

### Step 4: (Optional) Single-User Workstation

On a personal machine where every account is yours, you may prefer to skip the group and
make the counters world-readable. Per step 1, this mainly means any local process can
observe your machine's activity and defeat KASLR:

```bash
sudo tee /etc/udev/rules.d/99-codecarbon-rapl.rules <<'EOF'
SUBSYSTEM=="powercap", ACTION=="add", TEST=="energy_uj", RUN+="/bin/chmod 0444 /sys%p/energy_uj"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=powercap --action=add
```

### Alternative: sysfsutils (Debian and Ubuntu Only)

If you prefer a declarative configuration file, `sysfsutils` applies sysfs permissions at
boot through its own `systemd` unit. It is only packaged for Debian-based distributions,
and each RAPL domain must be listed explicitly:

```bash
sudo apt install sysfsutils
sudo tee -a /etc/sysfs.conf <<'EOF'
mode class/powercap/intel-rapl:0/energy_uj = 0440
owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon
mode class/powercap/intel-rapl:0:0/energy_uj = 0440
owner class/powercap/intel-rapl:0:0/energy_uj = root:codecarbon
EOF
sudo systemctl restart sysfsutils
```

Add one `mode` and one `owner` line per domain reported by `ls /sys/class/powercap/`.
Missing a domain is easy here, which is why the `udev` rule is preferred.

### Step 5: Verify RAPL Access

Test that CodeCarbon can now read RAPL data:

```bash
python -c "from codecarbon import EmissionsTracker; t = EmissionsTracker(); t.start(); import time; time.sleep(5); print(t.stop())"
```

Check the output for `CPU Tracking Method: RAPL` to confirm RAPL is active.

## Docker and Containerized Environments

If running CodeCarbon in Docker, mount the RAPL sysfs:

```bash
docker run --device /sys/class/powercap:/sys/class/powercap:ro <image>
```

Or in `docker-compose.yml`:

```yaml
volumes:
  - /sys/class/powercap:/sys/class/powercap:ro
```

## Learn More

To understand RAPL in detail, including domain hierarchy, double-counting issues, and CodeCarbon's domain selection strategy, see:

- [RAPL Metrics Explanation](../explanation/rapl.md) — Technical details on how RAPL works
- [CodeCarbon Power Estimation](../explanation/power-estimation.md) — How CodeCarbon uses RAPL data

## Next Steps

- [Linux Service](linux-service.md) — Configure RAPL permissions when running CodeCarbon as a background service
- [SLURM](slurm.md) — Enable RAPL on HPC clusters
- [Configure CodeCarbon](configuration.md) — Customize which RAPL domains to measure
