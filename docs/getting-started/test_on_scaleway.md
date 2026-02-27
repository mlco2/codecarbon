# Test of CodeCarbon on Scaleway hardware {#test_on_scaleway}

We use Scaleway hardware to test CodeCarbon on a real-world scenario. We
use the following hardware:

- **EM-I120E-NVME**: AMD EPYC 8024P, 64 GB, 2×960 GB NVMe
- **EM-B112X-SSD**: 2× Intel Xeon E5-2620 v3 @ 2.40GHz

85 W TDP for the Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz

Choose Ubuntu as OS because new version of stress-ng is not available on
Debian 12 (Bookworm).

Connect to the server:

``` console
ssh ubuntu@51.159.214.207
```

Install and run the test:

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

To do a full code CPU load, we run the following command:

``` console
stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s
```

Get back the data from the server:

``` console
mkdir -p codecarbon/data/hardware/cpu_load_profiling/E3-1240/
scp ubuntu@51.159.214.207:/home/ubuntu/codecarbon/*.csv codecarbon/data/hardware/cpu_load_profiling/E5-1240/
```

You can now delete the server in the Scaleway console.

For the results, see the notebook XXX.
