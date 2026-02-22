# Parameters

A set of parameters are supported by API to help users provide additional details per project.

## Input Parameters

| Parameter | Description |
|-----------|-------------|
| `project_name` | Name of the project, defaults to `codecarbon` |
| `experiment_id` | Id of the experiment |
| `measure_power_secs` | Interval (in seconds) to measure hardware power usage, defaults to `15` |
| `tracking_mode` | `machine` - measure power of entire machine (default)<br>`process` - isolate tracked processes |
| `gpu_ids` | Comma-separated GPU ids to track. Can be integer indexes or prefixes to match GPU identifiers |
| `log_level` | Global log level: "debug", "info" (default), "warning", "error", or "critical" |
| `electricitymaps_api_token` | API token for electricitymaps.com (formerly co2signal.com) |
| `pue` | PUE (Power Usage Effectiveness) of the data center where the experiment runs |
| `wue` | WUE (Water Usage Effectiveness) - liters of water per kWh of electricity |
| `force_cpu_power` | Force CPU max power consumption in watts (TDP-based) |
| `force_ram_power` | Force RAM power consumption in watts |
| `rapl_include_dram` | Include DRAM in RAPL measurements on Linux (default: False) |
| `rapl_prefer_psys` | Prefer psys RAPL domain over package domains (default: False) |
| `allow_multiple_runs` | Allow multiple CodeCarbon instances on same machine (default: True since v3) |

> **Note:** PUE is a multiplication factor provided by the user. Old datacenters have PUE up to 2.2, new greener ones as low as 1.1.

If you use `CUDA_VISIBLE_DEVICES` to set GPUs, CodeCarbon will automatically populate `gpu_ids`. Manual `gpu_ids` overrides this.

## Output Parameters

| Parameter | Description |
|-----------|-------------|
| `save_to_file` | Save emissions data to file (default: True) |
| `output_dir` | Directory for emissions data output |
| `emissions_endpoint` | Endpoint for HTTP output |
| `grafana_token` | Token for Grafana integration |
| `prometheus_endpoint` | Endpoint for Prometheus metrics |
