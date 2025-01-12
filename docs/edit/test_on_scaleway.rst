.. _test_on_scaleway:


Test of CodeCarbon on Scaleway hardware
=======================================

We use Scaleway hardware to test CodeCarbon on a real-world scenario. We use the following hardware:


    EM-I120E-NVME   AMD EPYC 8024P     64 GB    2 x 960 GB NVMe
    EM-B112X-SSD    2 x Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz

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

ubuntu@sd-175544:~/codecarbon$ hatch run python examples/intel_rapl_show.py
Detailed RAPL Domain Information:
{
  "intel-rapl:1": {
    "name": "intel-rapl:1",
    "files": {
      "uevent": "",
      "energy_uj": "22464335801",
      "enabled": "0",
      "constraint_1_max_power_uw": "170000000",
      "constraint_1_time_window_us": "7808",
      "constraint_1_power_limit_uw": "102000000",
      "constraint_0_time_window_us": "9994240",
      "constraint_1_name": "short_term",
      "constraint_0_power_limit_uw": "85000000",
      "constraint_0_name": "long_term",
      "name": "package-1",
      "constraint_0_max_power_uw": "85000000",
      "max_energy_range_uj": "262143328850"
    },
    "subdomain_details": {}
  },
  "intel-rapl:0": {
    "name": "intel-rapl:0",
    "files": {
      "uevent": "",
      "energy_uj": "23712361659",
      "enabled": "0",
      "constraint_1_max_power_uw": "170000000",
      "constraint_1_time_window_us": "7808",
      "constraint_1_power_limit_uw": "102000000",
      "constraint_0_time_window_us": "9994240",
      "constraint_1_name": "short_term",
      "constraint_0_power_limit_uw": "85000000",
      "constraint_0_name": "long_term",
      "name": "package-0",
      "constraint_0_max_power_uw": "85000000",
      "max_energy_range_uj": "262143328850"
    },
    "subdomain_details": {}
  }
}

Potential RAM Domains:
Available Power Domains:
Starting Power Monitoring:
Power Consumption: 12.82 Watts
Power Consumption: 14.27 Watts
Power Consumption: 14.43 Watts

ubuntu@sd-175544:~/codecarbon$ lscpu
Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          46 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   24
  On-line CPU(s) list:    0-23
Vendor ID:                GenuineIntel
  Model name:             Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz
    CPU family:           6
    Model:                63
    Thread(s) per core:   2
    Core(s) per socket:   6
    Socket(s):            2
    Stepping:             2
    CPU(s) scaling MHz:   41%
    CPU max MHz:          3200.0000
    CPU min MHz:          1200.0000
    BogoMIPS:             4799.72
    Flags:                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_
                          tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pd
                          cm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm cpuid_fault epb pti ssbd ibrs ibpb stibp tpr_shadow fle
                          xpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid cqm xsaveopt cqm_llc cqm_occup_llc dtherm ida arat pln pts vnmi md_clear flush_
                          l1d
Virtualization features:
  Virtualization:         VT-x
Caches (sum of all):
  L1d:                    384 KiB (12 instances)
  L1i:                    384 KiB (12 instances)
  L2:                     3 MiB (12 instances)
  L3:                     30 MiB (2 instances)
NUMA:
  NUMA node(s):           2
  NUMA node0 CPU(s):      0,2,4,6,8,10,12,14,16,18,20,22
  NUMA node1 CPU(s):      1,3,5,7,9,11,13,15,17,19,21,23
Vulnerabilities:
  Gather data sampling:   Not affected
  Itlb multihit:          KVM: Mitigation: VMX disabled
  L1tf:                   Mitigation; PTE Inversion; VMX conditional cache flushes, SMT vulnerable
  Mds:                    Mitigation; Clear CPU buffers; SMT vulnerable
  Meltdown:               Mitigation; PTI
  Mmio stale data:        Mitigation; Clear CPU buffers; SMT vulnerable
  Reg file data sampling: Not affected
  Retbleed:               Not affected
  Spec rstack overflow:   Not affected
  Spec store bypass:      Mitigation; Speculative Store Bypass disabled via prctl
  Spectre v1:             Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:             Mitigation; Retpolines; IBPB conditional; IBRS_FW; STIBP conditional; RSB filling; PBRSB-eIBRS Not affected; BHI Not affected
  Srbds:                  Not affected
  Tsx async abort:        Not affected

ubuntu@sd-175544:~/codecarbon$ hatch run python
Python 3.12.3 (main, Nov  6 2024, 18:32:19) [GCC 13.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from cpuinfo import get_cpu_info
>>> get_cpu_info()
{'python_version': '3.12.3.final.0 (64 bit)', 'cpuinfo_version': [9, 0, 0], 'cpuinfo_version_string': '9.0.0', 'arch': 'X86_64', 'bits': 64, 'count': 24, 'arch_string_raw': 'x86_64', 'vendor_id_raw': 'GenuineIntel', 'brand_raw': 'Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz', 'hz_advertised_friendly': '2.4000 GHz', 'hz_actual_friendly': '2.3737 GHz', 'hz_advertised': [2400000000, 0], 'hz_actual': [2373723000, 0], 'stepping': 2, 'model': 63, 'family': 6, 'flags': ['abm', 'acpi', 'aes', 'aperfmperf', 'apic', 'arat', 'arch_perfmon', 'avx', 'avx2', 'bmi1', 'bmi2', 'bts', 'clflush', 'cmov', 'constant_tsc', 'cpuid', 'cpuid_fault', 'cqm', 'cqm_llc', 'cqm_occup_llc', 'cx16', 'cx8', 'dca', 'de', 'ds_cpl', 'dtes64', 'dtherm', 'dts', 'epb', 'ept', 'ept_ad', 'erms', 'est', 'f16c', 'flexpriority', 'flush_l1d', 'fma', 'fpu', 'fsgsbase', 'fxsr', 'ht', 'ibpb', 'ibrs', 'ida', 'invpcid', 'lahf_lm', 'lm', 'mca', 'mce', 'md_clear', 'mmx', 'monitor', 'movbe', 'msr', 'mtrr', 'nonstop_tsc', 'nopl', 'nx', 'osxsave', 'pae', 'pat', 'pbe', 'pcid', 'pclmulqdq', 'pdcm', 'pdpe1gb', 'pebs', 'pge', 'pln', 'pni', 'popcnt', 'pqm', 'pse', 'pse36', 'pti', 'pts', 'rdrand', 'rdrnd', 'rdtscp', 'rep_good', 'sdbg', 'sep', 'smep', 'smx', 'ss', 'ssbd', 'sse', 'sse2', 'sse4_1', 'sse4_2', 'ssse3', 'stibp', 'syscall', 'tm', 'tm2', 'tpr_shadow', 'tsc', 'tsc_adjust', 'tsc_deadline_timer', 'tscdeadline', 'vme', 'vmx', 'vnmi', 'vpid', 'x2apic', 'xsave', 'xsaveopt', 'xtopology', 'xtpr'], 'l3_cache_size': 15728640, 'l2_cache_size': 3145728, 'l1_data_cache_size': 393216, 'l1_instruction_cache_size': 393216, 'l2_cache_line_size': 256, 'l2_cache_associativity': 6}
>>>


Is NUMA node(s) giving the number of physical CPU?

ubuntu@sd-175544:~/codecarbon$ sudo dmidecode -t 4
# dmidecode 3.5
Getting SMBIOS data from sysfs.
SMBIOS 2.8 present.

Handle 0x0400, DMI type 4, 42 bytes
Processor Information
	Socket Designation: CPU1
	Type: Central Processor
	Family: Xeon
	Manufacturer: Intel
	ID: F2 06 03 00 FF FB EB BF
	Signature: Type 0, Family 6, Model 63, Stepping 2
	Flags:
		FPU (Floating-point unit on-chip)
		VME (Virtual mode extension)
		DE (Debugging extension)
		PSE (Page size extension)
		TSC (Time stamp counter)
		MSR (Model specific registers)
		PAE (Physical address extension)
		MCE (Machine check exception)
		CX8 (CMPXCHG8 instruction supported)
		APIC (On-chip APIC hardware supported)
		SEP (Fast system call)
		MTRR (Memory type range registers)
		PGE (Page global enable)
		MCA (Machine check architecture)
		CMOV (Conditional move instruction supported)
		PAT (Page attribute table)
		PSE-36 (36-bit page size extension)
		CLFSH (CLFLUSH instruction supported)
		DS (Debug store)
		ACPI (ACPI supported)
		MMX (MMX technology supported)
		FXSR (FXSAVE and FXSTOR instructions supported)
		SSE (Streaming SIMD extensions)
		SSE2 (Streaming SIMD extensions 2)
		SS (Self-snoop)
		HTT (Multi-threading)
		TM (Thermal monitor supported)
		PBE (Pending break enabled)
	Version: Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz
	Voltage: 1.3 V
	External Clock: 8000 MHz
	Max Speed: 4000 MHz
	Current Speed: 2400 MHz
	Status: Populated, Enabled
	Upgrade: Socket LGA2011-3
	L1 Cache Handle: 0x0700
	L2 Cache Handle: 0x0701
	L3 Cache Handle: 0x0702
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Core Count: 6
	Core Enabled: 6
	Thread Count: 12
	Characteristics:
		64-bit capable
		Multi-Core
		Hardware Thread
		Execute Protection
		Enhanced Virtualization
		Power/Performance Control

Handle 0x0401, DMI type 4, 42 bytes
Processor Information
	Socket Designation: CPU2
	Type: Central Processor
	Family: Xeon
	Manufacturer: Intel
	ID: F2 06 03 00 FF FB EB BF
	Signature: Type 0, Family 6, Model 63, Stepping 2
	Flags:
		FPU (Floating-point unit on-chip)
		VME (Virtual mode extension)
		DE (Debugging extension)
		PSE (Page size extension)
		TSC (Time stamp counter)
		MSR (Model specific registers)
		PAE (Physical address extension)
		MCE (Machine check exception)
		CX8 (CMPXCHG8 instruction supported)
		APIC (On-chip APIC hardware supported)
		SEP (Fast system call)
		MTRR (Memory type range registers)
		PGE (Page global enable)
		MCA (Machine check architecture)
		CMOV (Conditional move instruction supported)
		PAT (Page attribute table)
		PSE-36 (36-bit page size extension)
		CLFSH (CLFLUSH instruction supported)
		DS (Debug store)
		ACPI (ACPI supported)
		MMX (MMX technology supported)
		FXSR (FXSAVE and FXSTOR instructions supported)
		SSE (Streaming SIMD extensions)
		SSE2 (Streaming SIMD extensions 2)
		SS (Self-snoop)
		HTT (Multi-threading)
		TM (Thermal monitor supported)
		PBE (Pending break enabled)
	Version: Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz
	Voltage: 1.3 V
	External Clock: 8000 MHz
	Max Speed: 4000 MHz
	Current Speed: 2400 MHz
	Status: Populated, Enabled
	Upgrade: Socket LGA2011-3
	L1 Cache Handle: 0x0703
	L2 Cache Handle: 0x0704
	L3 Cache Handle: 0x0705
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Core Count: 6
	Core Enabled: 6
	Thread Count: 12
	Characteristics:
		64-bit capable
		Multi-Core
		Hardware Thread
		Execute Protection
		Enhanced Virtualization
		Power/Performance Control


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
