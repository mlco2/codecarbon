#!/bin/bash
find /sys/class/powercap/intel-rapl/* -name energy_uj -exec bash -c "echo {} && cat {}" \;
# cat /sys/class/powercap/intel-rapl/intel-rapl:1/energy_uj
# cat /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
python full_cpu.py
find /sys/class/powercap/intel-rapl/* -name energy_uj -exec bash -c "echo {} && cat {}" \;
# cat /sys/class/powercap/intel-rapl/intel-rapl:1/energy_uj
# cat /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
