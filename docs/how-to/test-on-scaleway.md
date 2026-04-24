# Test CodeCarbon on Scaleway Hardware {#test_on_scaleway}

This guide shows how to test CodeCarbon on real cloud hardware using Scaleway. Testing on actual hardware helps validate energy measurements and carbon tracking in production environments.

## Hardware Overview

The following Scaleway hardware configurations are available for testing:

- **EM-I120E-NVME**: AMD EPYC 8024P, 64 GB RAM, 2×960 GB NVMe SSD
- **EM-B112X-SSD**: 2× Intel Xeon E5-2620 v3 @ 2.40GHz (85 W TDP)

## Prerequisites

- Scaleway account with hardware access
- Ubuntu as the OS (required for latest stress-ng tools; Debian 12 packages are outdated)
- SSH access to the server

## Setup Steps

### Step 1: Connect to Your Scaleway Server

``` console
ssh ubuntu@<your-server-ip>
```

### Step 2: Install Dependencies and CodeCarbon

Install the necessary tools and CodeCarbon on the server:

``` console
sudo chmod a+r -R /sys/class/powercap/intel-rapl/subsystem/*
sudo apt update && sudo apt install -y git pipx python3-launchpadlib htop
pipx ensurepath
sudo add-apt-repository -y ppa:colin-king/stress-ng
sudo apt update && sudo apt install -y stress-ng
export PATH=$PATH:/home/ubuntu/.local/bin
git clone https://github.com/mlco2/codecarbon.git
cd codecarbon
git checkout use-cpu-load
curl -LsSf https://astral.sh/uv/install.sh | sh
uv run python examples/compare_cpu_load_and_RAPL.py
```

### Step 3: Run CPU Load Test

Execute a full CPU load test using stress-ng to measure power consumption:

``` console
stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s
```

### Step 4: Retrieve Test Results

Download the measurement data from the server to your local machine:

``` console
mkdir -p codecarbon/data/hardware/cpu_load_profiling/E3-1240/
scp ubuntu@<your-server-ip>:/home/ubuntu/codecarbon/*.csv codecarbon/data/hardware/cpu_load_profiling/E5-1240/
```

### Step 5: Clean Up

Delete the server in the Scaleway console to avoid ongoing charges.

## Results and Analysis

The CSV files contain measurement data from both CodeCarbon and the stress-ng tool. You can analyze the results using Jupyter notebooks or other data analysis tools.

## Next Steps

- [Configure CodeCarbon](configuration.md) for different measurement intervals or tracking modes
- [Send emissions data to the cloud](cloud-api.md) for centralized tracking
- Review hardware-specific RAPL configuration in [RAPL Metrics](../explanation/rapl.md)
