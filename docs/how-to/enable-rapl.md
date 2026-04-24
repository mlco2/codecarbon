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

Due to [CVE-2020-8694](https://www.cve.org/CVERecord?id=CVE-2020-8694), Linux distributions restrict RAPL file permissions to root-only for security. This prevents unprivileged users from reading fine-grained power data.

### Step 2: Temporary Access (Testing)

To quickly test RAPL without permanent changes:

```bash
sudo chmod -R a+r /sys/class/powercap/*
```

This grants read access to all users. However, **permissions are lost at next reboot**, so this is only for testing.

### Step 3: Permanent Access (Recommended)

For permanent access that survives reboots, use `sysfsutils`:

**Step 3a: Install sysfsutils**

```bash
sudo apt install sysfsutils
```

**Step 3b: Configure RAPL Permissions**

Edit the sysfsutils configuration:

```bash
sudo nano /etc/sysfs.conf
```

Add this line at the end:

```text
mode class/powercap/intel-rapl:0/energy_uj = 0444
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

**Step 3c: Reboot to Apply Changes**

```bash
sudo reboot
```

### Step 4: (Optional) More Restrictive Permissions

For better security, you can create a dedicated group instead of allowing all users:

```bash
# Create a codecarbon group
sudo groupadd codecarbon

# Add your user to the group
sudo usermod -a -G codecarbon $USER

# Update sysfs.conf with group permissions
sudo nano /etc/sysfs.conf
```

Update the line to:

```text
mode class/powercap/intel-rapl:0/energy_uj = 0440
owner class/powercap/intel-rapl:0/energy_uj = root:codecarbon
```

Log out and back in for group membership to take effect:

```bash
logout
# Then log back in
```

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
