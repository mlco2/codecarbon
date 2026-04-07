# Contributions

Added a function in Hardware.py that tracks cpu temps live in Celsius, this covers issue 1008

### Added code

``` python
def get_cpu_temperature(self) -> float:
        """
        Get average CPU temperature in Celsius.
        Supported on Linux (Intel + AMD) and Windows Intel via Power Gadget.
        Returns 0.0 if temperature cannot be read on the current platform.
        """
        try:
            if self._mode == "intel_power_gadget":
                all_cpu_details = self._intel_interface.get_cpu_details()
                for metric, value in all_cpu_details.items():
                    if re.match(r"^CPU Temperature", metric):
                        return float(value)
                return 0.0

            elif self._mode in ["intel_rapl", MODE_CPU_LOAD, "constant"]:
                temps = psutil.sensors_temperatures()
                if not temps:
                    logger.debug(
                        "get_cpu_temperature: psutil.sensors_temperatures() "
                        "returned no data on this platform"
                    )
                    return 0.0
                for key in ["coretemp", "k10temp", "cpu_thermal"]:
                    if key in temps:
                        readings = temps[key]
                        avg = sum(r.current for r in readings) / len(readings)
                        logger.debug(f"get_cpu_temperature: {key} avg = {avg:.1f}°C")
                        return avg
                return 0.0

        except Exception as e:
            logger.debug(f"get_cpu_temperature: Could not read CPU temperature: {e}")
            return 0.0
```

Allowed for CodeCarbon to track it and input it in to the CSV data set, shown in terminal below
![](../images/CpuTemp.png){.align-center width="700px" height="400px"}

Make sure to run the 'test_temp.py' file
