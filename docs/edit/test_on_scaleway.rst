.. _test_on_scaleway:


Test of CodeCarbon on Scaleway hardware
=======================================

We use Scaleway hardware to test CodeCarbon on a real-world scenario. We use the following hardware:


    EM-I120E-NVME   AMD EPYC 8024P     64 GB    2 x 960 GB NVMe
    EM-B112X-SSD    Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz

85 W TDP for the Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz

Choose Ubuntu as OS because new version of stress-ng is not available on Debian 12 (Bookworm).

.. code-block:: console

    ssh ubuntu@51.159.214.207
    sudo chmod a+r -R /sys/class/powercap/intel-rapl/*
    sudo apt update && sudo apt install -y git pipx python3-launchpadlib htop
    pipx ensurepath
    sudo add-apt-repository -y ppa:colin-king/stress-ng
    sudo apt update && sudo apt install -y stress-ng
    export PATH=$PATH:/home/ubuntu/.local/bin
    git clone https://github.com/mlco2/codecarbon.git
    cd codecarbon
    git checkout use-cpu-load
    pipx install hatch
    hatch run python examples/compare_cpu_load_and_RAPL.py

To do a full code CPU load, we run the following command:

.. code-block:: console

    stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s


Get back the data from the server:

.. code-block:: console

        mkdir -p codecarbon/data/hardware/cpu_load_profiling/E3-1240/
        scp ubuntu@51.158.62.235:/home/ubuntu/codecarbon/*.csv codecarbon/data/hardware/cpu_load_profiling/E3-1240/

AMD EPYC 8024P 8-Core Processor TDP : 90 W

What we learn

We have to find what the real TDP of CPU is. Because for the Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz, the TDP is 85 W, but the real TDP seems to be 60 W.

$ stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s
stress-ng: info:  [9573] setting to a 1 min run per stressor
stress-ng: info:  [9573] dispatching hogs: 24 cpu
stress-ng: metrc: [9573] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: metrc: [9573]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: metrc: [9573] cpu              614145     60.00   1439.79      0.04     10235.00         426.54
stress-ng: info:  [9573] Cannot read perf counters, do not have CAP_SYS_ADMIN capability or /proc/sys/kernel/perf_event_paranoid is set too high (4)
stress-ng: info:  [9573] cpu:
stress-ng: info:  [9573]  dram                    6.09 W
stress-ng: info:  [9573]  pkg-0                  51.78 W
stress-ng: info:  [9573]  pkg-1                  54.41 W
stress-ng: info:  [9573] skipped: 0
stress-ng: info:  [9573] passed: 24: cpu (24)
stress-ng: info:  [9573] failed: 0
stress-ng: info:  [9573] metrics untrustworthy: 0
stress-ng: info:  [9573] successful run completed in 1 min



For the AMD EPYC 8024P 8-Core Processor, the TDP is 90 W, but the real TDP seems to be 60 W.

For Threadripper 1950X

stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s
stress-ng: info:  [135178] setting to a 1 min run per stressor
stress-ng: info:  [135178] dispatching hogs: 128 cpu
stress-ng: metrc: [135178] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: metrc: [135178]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: metrc: [135178] cpu             1028008     60.02   1908.89      0.59     17128.73         538.37
stress-ng: info:  [135178] Cannot read perf counters, do not have CAP_SYS_ADMIN capability or /proc/sys/kernel/perf_event_paranoid is set too high (4)
stress-ng: info:  [135178] cpu:
stress-ng: info:  [135178]  core                    8.57 W
stress-ng: info:  [135178]  pkg-0-die-0           169.95 W
stress-ng: info:  [135178]  pkg-0-die-1           169.95 W
stress-ng: info:  [135178] skipped: 0
stress-ng: info:  [135178] passed: 128: cpu (128)
stress-ng: info:  [135178] failed: 0
stress-ng: info:  [135178] metrics untrustworthy: 0
stress-ng: info:  [135178] successful run completed in 1 min

Intel(R) Xeon(R) CPU E3-1240 V2 @ 3.40GHz

$ stress-ng --cpu 0 --cpu-method matrixprod --metrics-brief --rapl --perf -t 60s
stress-ng: info:  [5175] setting to a 1 min run per stressor
stress-ng: info:  [5175] dispatching hogs: 8 cpu
stress-ng: metrc: [5175] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: metrc: [5175]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: metrc: [5175] cpu              342094     60.00    475.41      0.94      5701.11         718.15
stress-ng: info:  [5175] Cannot read perf counters, do not have CAP_SYS_ADMIN capability or /proc/sys/kernel/perf_event_paranoid is set too high (4)
stress-ng: info:  [5175] cpu:
stress-ng: info:  [5175]  core                   40.44 W
stress-ng: info:  [5175]  pkg-0                  44.00 W
stress-ng: info:  [5175] skipped: 0
stress-ng: info:  [5175] passed: 8: cpu (8)
stress-ng: info:  [5175] failed: 0
stress-ng: info:  [5175] metrics untrustworthy: 0
stress-ng: info:  [5175] successful run completed in 1 min
