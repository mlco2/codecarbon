# API Reference

Parameters can be set via `EmissionsTracker()`, `OfflineEmissionsTracker()`, the `@track_emissions` decorator, config files, or environment variables. See [Configuration](<https://docs.codecarbon.io/latest/how-to/configuration/index.md>) for priority order.

> [!NOTE]
>
> **PUE**
>
> PUE is a multiplication factor provided by the user. Old datacenters have PUE up to 2.2, new greener ones as low as 1.1.

> [!NOTE]
>
> **GPU selection**
>
> If you use `CUDA_VISIBLE_DEVICES` or `ROCR_VISIBLE_DEVICES` to set GPUs, CodeCarbon will automatically populate `gpu_ids`. Manual `gpu_ids` overrides this.

## EmissionsTracker / BaseEmissionsTracker

`EmissionsTracker` and `OfflineEmissionsTracker` inherit from `BaseEmissionsTracker`. All parameters are documented below:

## `codecarbon.emissions_tracker.BaseEmissionsTracker`

Bases: `ABC`

Primary abstraction with Emissions Tracking functionality. Has two abstract methods, `_get_geo_metadata` and `_get_cloud_metadata` that are implemented by two concrete classes: `OfflineCarbonTracker` and `CarbonTracker.`

Parameters:

<table>       <thead>         <tr>           <th>Name</th>           <th>Type</th>           <th>Description</th>           <th>Default</th>         </tr>       </thead>       <tbody>           <tr class="doc-section-item">             <td>                 <code>project_name</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Project name for current experiment run, default name is &quot;codecarbon&quot;.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>measure_power_secs</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="float">float</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Interval (in seconds) to measure hardware power usage, defaults to 15.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>api_call_interval</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="int">int</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Number of measurements between API calls (default: 8). -1: call API only on flush() and at the end. 1: at every measure. 2: every 2 measures, and so on.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>api_endpoint</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Optional URL of Code Carbon API endpoint for sending emissions data.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>api_key</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>API key for Code Carbon API (mandatory!).</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>output_dir</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Directory path to which the experiment details are logged, defaults to current directory.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>output_file</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Name of the output CSV file, defaults to <code>emissions.csv</code>.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>output_methods</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="typing.List">List</span>[<span title="codecarbon.output_methods.base_output.OutputMethod">OutputMethod</span>]]</code>             </td>             <td>               <div class="doc-md-description">                 <p>List of :class:<code>OutputMethod</code> enum values specifying where to send emissions data. Example::</p> <div class="highlight"><pre><span></span><code>EmissionsTracker(output_methods=[OutputMethod.CSV, OutputMethod.API])&#10;</code></pre></div> <p>Available values: <code>CSV</code>, <code>API</code>, <code>LOGGER</code>, <code>PROMETHEUS</code>, <code>LOGFIRE</code>, <code>BOAMPS</code>, <code>SCI</code>. When provided, the individual <code>save_to_*</code> flags are ignored. Defaults to <code>[OutputMethod.CSV]</code>. Can also be set in config as a comma-separated string: <code>output_methods=csv,api</code>. (HTTP output is enabled separately via <code>emissions_endpoint</code>.)</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>save_to_file</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use <code>output_methods</code> instead. Indicates if the emission artifacts should be logged to a file, defaults to True.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>save_to_api</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use <code>output_methods</code> instead. Indicates if the emission artifacts should be sent to the CodeCarbon API, defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>save_to_logger</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use <code>output_methods</code> instead. Indicates if the emission artifacts should be written to a dedicated logger, defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>logging_logger</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="codecarbon.output_methods.logger.LoggerOutput">LoggerOutput</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>LoggerOutput object encapsulating a logging.logger or a Google Cloud logger.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>save_to_prometheus</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use <code>output_methods</code> instead. Indicates if the emission artifacts should be pushed to prometheus, defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>save_to_logfire</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use <code>output_methods</code> instead. Indicates if the emission artifacts should be written to a logfire observability platform, defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>prometheus_url</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>url of the prometheus server, defaults to <code>localhost:9091</code>.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>output_handlers</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="typing.List">List</span>[<span title="codecarbon.output_methods.base_output.BaseOutput">BaseOutput</span>]]</code>             </td>             <td>               <div class="doc-md-description">                 <p>List of custom output handlers to use. Defaults to [].</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>gpu_ids</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="typing.List">List</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Comma-separated list of GPU ids to track, defaults to None. Can be integer indexes of GPUs on the system, or prefixes to match against GPU identifiers. See NVIDIA docs on CUDA environment variables.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>emissions_endpoint</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Optional URL of http endpoint for sending emissions data.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>experiment_id</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Id of the experiment.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>experiment_name</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Label of the experiment</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>electricitymaps_api_token</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>API token for electricitymaps.com (formerly co2signal.com)</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>co2_signal_api_token</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>[DEPRECATED] Use electricitymaps_api_token instead. Old parameter name for backward compatibility.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>tracking_mode</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>One of &quot;process&quot; or &quot;machine&quot; in order to measure the power consumption due to the entire machine or to try and isolate the tracked processe's in isolation. Defaults to &quot;machine&quot;.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>log_level</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="typing.Union">Union</span>[<span title="int">int</span>, <span title="str">str</span>]]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Global codecarbon log level. Accepts one of:   {&quot;debug&quot;, &quot;info&quot;, &quot;warning&quot;, &quot;error&quot;, &quot;critical&quot;}. Defaults to &quot;info&quot;.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>on_csv_write</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>When calling tracker.flush() manually: &quot;update&quot; to overwrite the existing run_id row, or &quot;append&quot; to add a new row to the CSV file. Defaults to &quot;append&quot;.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>live_output_file</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Optional CSV filename for interval measurement export. When set, CodeCarbon appends a row on the same cadence as API/Prometheus (<code>api_call_interval * measure_power_secs</code>). Use <code>&quot;auto&quot;</code> (or an empty string) to name the file <code>emissions_&lt;run_id&gt;.csv</code>. Defaults to None (disabled).</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>logger_preamble</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="str">str</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>String to systematically include in the logger. messages. Defaults to &quot;&quot;.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>force_cpu_power</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="int">int</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Force the CPU max power consumption in watts. Use this if you know the TDP of your machine.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>force_ram_power</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="int">int</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Force the RAM power consumption in watts. Use this if you know the power consumption of your RAM. Estimate with <code>sudo lshw -C memory -short | grep DIMM</code> to get RAM slots, then RAM power (W) = Number of RAM Slots × 5 Watts.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>pue</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="float">float</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>PUE (Power Usage Effectiveness) of the data center where the experiment is being run. It multiplies both the reported power and the reported energy, including forced values: with <code>force_cpu_power=100</code> and <code>pue=1.5</code> the CPU is reported at 150 W.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>wue</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="float">float</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>WUE (Water Usage Effectiveness) of the data center. Units of L/kWh: litres of water consumed per kilowatt-hour of electricity consumed.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>force_carbon_intensity_g_co2e_kwh</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="float">float</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Override grid carbon intensity in gCO2e/kWh for emissions calculations.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>force_mode_cpu_load</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Force the addition of a CPU in MODE_CPU_LOAD</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>force_mode_constant</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Estimate CPU power as a constant fraction of the CPU TDP (or of <code>force_cpu_power</code>), skipping RAPL, Power Gadget, powermetrics and CPU load tracking. Takes precedence over <code>force_mode_cpu_load</code>. Defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>allow_multiple_runs</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Allow multiple CodeCarbon instances on the same machine. Defaults to True since v3 (was False in v2).</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>rapl_include_dram</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Include DRAM (memory) power in the counter-based CPU measurements, defaults to False. When True, measures CPU package + DRAM. Applies to the Linux RAPL interface and to the Windows Energy Meter Interface, on systems exposing separate DRAM domains/channels.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>rapl_prefer_psys</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Prefer psys (platform) RAPL domain over package domains on Linux, defaults to False. When True, uses total platform power (CPU + chipset + PCIe). When False, uses package domains which are more reliable. Note: psys can report higher values than CPU TDP and may be unreliable on older systems.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>metadata</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="typing.Union">Union</span>[<span title="dict">dict</span>, <span title="str">str</span>]]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Free-form metadata bag to enrich outputs. Either a dict or a path to a JSON file containing a dict. Individual output methods read their own section from it. When <code>OutputMethod.BOAMPS</code> is used, the <code>boamps</code> key (or, for backward compatibility, the whole dict) is read following the BoAmps schema structure (with <code>task</code>, <code>header</code>, <code>quality</code>, <code>infrastructure</code>, <code>environment</code> sections) to fill the required BoAmps fields (taskStage, taskFamily, algorithms, dataset) that cannot be auto-detected by CodeCarbon. Can also be set in config as a path to a JSON file: <code>metadata=metadata.json</code>.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>           <tr class="doc-section-item">             <td>                 <code>use_national_grid_eso_api</code>             </td>             <td>                   <code><span title="typing.Optional">Optional</span>[<span title="bool">bool</span>]</code>             </td>             <td>               <div class="doc-md-description">                 <p>Opt-in: when True and the detected location is Great Britain, fetch live carbon intensity from the UK National Grid ESO Carbon Intensity API (https://carbonintensity.org.uk/, Open Government Licence v3.0) instead of CodeCarbon's static country-average data. This makes a network call (4 s timeout, value cached for 5 minutes per process, back-off after a failure) and reports a Great-Britain-wide figure, not a regional one. Defaults to False.</p>               </div>             </td>             <td>                   <code><span title="codecarbon.emissions_tracker._sentinel">_sentinel</span></code>             </td>           </tr>       </tbody>     </table>

### Methods

Bases: `ABC`

Primary abstraction with Emissions Tracking functionality. Has two abstract methods, `_get_geo_metadata` and `_get_cloud_metadata` that are implemented by two concrete classes: `OfflineCarbonTracker` and `CarbonTracker.`

#### `start()`

Starts tracking the experiment. Currently, Nvidia GPUs are supported.

Returns:

| Type | Description |
| --- | --- |
| `None` | None |

#### `stop()`

Stops tracking the experiment

Returns:

| Type | Description |
| --- | --- |
| `Optional[float]` | CO2 emissions in kgs |

#### `flush()`

Write the emissions to disk or call the API depending on the configuration, but keep running the experiment.

Returns:

| Type | Description |
| --- | --- |
| `Optional[float]` | CO2 emissions in kgs |

#### `start_task(task_name=None)`

Start tracking a dedicated execution task.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `task_name` |  | Name of the task to be isolated. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `None` | None |

#### `stop_task(task_name=None)`

Stop tracking a dedicated execution task. Delta energy is computed by task, to isolate its contribution to total emissions.

Returns:

| Type | Description |
| --- | --- |
| `EmissionsData` | EmissionData for an execution task |

#### `get_detected_hardware()`

Get the detected hardware.

Returns:

| Type | Description |
| --- | --- |
| `Dict[str, Any]` | A dictionary containing hardware data. |

#### `service_shutdown(signum, frame)`

Signal handler that stops the tracker on SIGTERM/SIGINT, for use when CodeCarbon runs as a long-lived service. Register it with:

```
import signal

tracker = EmissionsTracker()
signal.signal(signal.SIGTERM, tracker.service_shutdown)
signal.signal(signal.SIGINT, tracker.service_shutdown)
```

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `signum` |  | Signal number, passed by `signal.signal` | *required* |
| `frame` |  | Current stack frame, passed by `signal.signal` | *required* |

Returns:

| Type | Description |
| --- | --- |
|  | None |

## OfflineEmissionsTracker (additional parameters)

`OfflineEmissionsTracker` adds these parameters for offline mode:

## `codecarbon.emissions_tracker.OfflineEmissionsTracker`

Bases: `BaseEmissionsTracker`

Offline implementation of the `EmissionsTracker` In addition to the standard arguments, the following are required.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `country_iso_code` | `Optional[str]` | 3-letter ISO code of the country where the experiment is being run. See global\_energy\_mix.json for available countries. | `_sentinel` |
| `region` | `Optional[str]` | Optional Province/State/City where the infrastructure is hosted. Supported for US States and Canada (e.g. California, New York). | `_sentinel` |
| `cloud_provider` | `Optional[str]` | The cloud provider specified for estimating emissions intensity, defaults to None. See https://github.com/mlco2/codecarbon/ blob/master/codecarbon/data/cloud/impact.csv for a list of cloud providers | `_sentinel` |
| `cloud_region` | `Optional[str]` | The region of the cloud data center, defaults to None. See https://github.com/mlco2/codecarbon/ blob/master/codecarbon/data/cloud/impact.csv for a list of cloud regions. | `_sentinel` |
| `country_2letter_iso_code` | `Optional[str]` | For use with the Electricity Maps emissions API. See http://api.electricitymap.org/v3/zones for a list of codes and their corresponding locations. | `_sentinel` |

## @track\_emissions Decorator

The decorator accepts the same parameters as `EmissionsTracker`, plus `offline` and `country_iso_code` for offline mode. It does not accept `force_mode_cpu_load` or `metadata` as arguments. Set them in the config file, with the `CODECARBON_FORCE_MODE_CPU_LOAD` and `CODECARBON_METADATA` environment variables, or use `EmissionsTracker` directly:

## `codecarbon.emissions_tracker.track_emissions`

Decorator that supports both `EmissionsTracker` and `OfflineEmissionsTracker`

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `fn` | `Callable` | Function to be decorated | `None` |
| `project_name` | `Optional[str]` | Project name for current experiment run, default name is "codecarbon". | `_sentinel` |
| `measure_power_secs` | `Optional[int]` | Interval (in seconds) to measure hardware power usage, defaults to 15. | `_sentinel` |
| `api_call_interval` | `int` | Number of measurements between API calls (default: 8). -1: call API only on flush() and at the end. 1: at every measure. 2: every 2 measures, and so on. | `_sentinel` |
| `api_endpoint` | `Optional[str]` | Optional URL of Code Carbon API endpoint for sending emissions data. | `_sentinel` |
| `api_key` | `Optional[str]` | API key for Code Carbon API (mandatory!). | `_sentinel` |
| `output_dir` | `Optional[str]` | Directory path to which the experiment details are logged, defaults to current directory. | `_sentinel` |
| `output_file` | `Optional[str]` | Name of output CSV file, defaults to `emissions.csv` | `_sentinel` |
| `output_methods` | `Optional[List[OutputMethod]]` | List of OutputMethod enum values. See BaseEmissionsTracker. | `_sentinel` |
| `save_to_file` | `Optional[bool]` | \[DEPRECATED\] Use output\_methods instead. | `_sentinel` |
| `save_to_api` | `Optional[bool]` | \[DEPRECATED\] Use output\_methods instead. | `_sentinel` |
| `save_to_logger` | `Optional[bool]` | \[DEPRECATED\] Use output\_methods instead. | `_sentinel` |
| `logging_logger` | `Optional[LoggerOutput]` | LoggerOutput object encapsulating a logging.logger or a Google Cloud logger. | `_sentinel` |
| `save_to_prometheus` | `Optional[bool]` | \[DEPRECATED\] Use output\_methods instead. | `_sentinel` |
| `save_to_logfire` | `Optional[bool]` | \[DEPRECATED\] Use output\_methods instead. | `_sentinel` |
| `prometheus_url` | `Optional[str]` | url of the prometheus server, defaults to `localhost:9091`. | `_sentinel` |
| `output_handlers` | `Optional[List[BaseOutput]]` | List of output handlers to use. | `_sentinel` |
| `gpu_ids` | `Optional[List]` | User-specified known gpu ids to track. Defaults to None, which means that all available gpus will be tracked. It needs to be a list of integers or a comma-separated string. Valid examples: \[1, 3, 4\] or "1,2". | `_sentinel` |
| `emissions_endpoint` | `Optional[str]` | Optional URL of http endpoint for sending emissions data. | `_sentinel` |
| `experiment_id` | `Optional[str]` | Id of the experiment. | `_sentinel` |
| `experiment_name` | `Optional[str]` | Label of the experiment | `_sentinel` |
| `electricitymaps_api_token` | `Optional[str]` | API token for electricitymaps.com (formerly co2signal.com) | `_sentinel` |
| `co2_signal_api_token` | `Optional[str]` | \[DEPRECATED\] Use electricitymaps\_api\_token instead. Old parameter name for backward compatibility. | `_sentinel` |
| `tracking_mode` | `Optional[str]` | One of "process" or "machine" in order to measure the power consumption due to the entire machine or to try and isolate the tracked processe's in isolation. Defaults to "machine". | `_sentinel` |
| `log_level` | `Optional[Union[int, str]]` | Global codecarbon log level. Accepts one of: {"debug", "info", "warning", "error", "critical"}. Defaults to "info". | `_sentinel` |
| `on_csv_write` | `Optional[str]` | When calling tracker.flush() manually: "update" to overwrite the existing run\_id row, or "append" to add a new row. Defaults to "append". | `_sentinel` |
| `live_output_file` | `Optional[str]` | Optional CSV filename for interval measurement export. See EmissionsTracker. Defaults to None (disabled). | `_sentinel` |
| `logger_preamble` | `Optional[str]` | String to systematically include in the logger. messages. Defaults to "". | `_sentinel` |
| `allow_multiple_runs` | `Optional[bool]` | Allow multiple CodeCarbon instances on the same machine. Defaults to True since v3 (was False in v2). | `_sentinel` |
| `offline` | `Optional[bool]` | Run the tracker in offline mode, defaults to False. | `_sentinel` |
| `country_iso_code` | `Optional[str]` | 3-letter ISO code of the country where the experiment is being run. Required if offline=True. See global\_energy\_mix.json. | `_sentinel` |
| `region` | `Optional[str]` | Optional Province/State/City where the infrastructure is hosted. Supported for US States and Canada (e.g. California, New York). | `_sentinel` |
| `cloud_provider` | `Optional[str]` | The cloud provider specified for estimating emissions intensity, defaults to None. See https://github.com/mlco2/codecarbon/ blob/master/codecarbon/data/cloud/impact.csv for a list of cloud providers. | `_sentinel` |
| `cloud_region` | `Optional[str]` | The region of the cloud data center, defaults to None. See https://github.com/mlco2/codecarbon/ blob/master/codecarbon/data/cloud/impact.csv for a list of cloud regions. | `_sentinel` |
| `country_2letter_iso_code` | `Optional[str]` | For use with the Electricity Maps emissions API. See http://api.electricitymap.org/v3/zones for a list of codes and their corresponding locations. | `_sentinel` |
| `force_cpu_power` | `Optional[int]` | Force the CPU max power consumption in watts. Use if you know the TDP of your machine. | `_sentinel` |
| `force_ram_power` | `Optional[int]` | Force the RAM power consumption in watts. Estimate with `sudo lshw -C memory -short \| grep DIMM` for RAM slots, then RAM power (W) = Number of RAM Slots × 5 Watts. | `_sentinel` |
| `pue` | `Optional[float]` | PUE (Power Usage Effectiveness) of the data center. It multiplies both the reported power and the reported energy, including forced values: with `force_cpu_power=100` and `pue=1.5` the CPU is reported at 150 W. | `_sentinel` |
| `wue` | `Optional[float]` | WUE (Water Usage Effectiveness) of the data center. Units of L/kWh: litres of water consumed per kilowatt-hour of electricity consumed. | `_sentinel` |
| `force_carbon_intensity_g_co2e_kwh` | `Optional[float]` | Override grid carbon intensity in gCO2e/kWh for emissions calculations. | `_sentinel` |
| `force_mode_cpu_load` | `Optional[bool]` | Force the addition of a CPU in MODE\_CPU\_LOAD. | `_sentinel` |
| `force_mode_constant` | `Optional[bool]` | Estimate CPU power as a constant fraction of the CPU TDP (or of `force_cpu_power`), skipping RAPL, Power Gadget, powermetrics and CPU load tracking. Takes precedence over `force_mode_cpu_load`. Defaults to False. | `_sentinel` |
| `rapl_include_dram` | `Optional[bool]` | Include DRAM in the counter-based CPU measurements (Linux RAPL and Windows EMI, default: False). When True, measures CPU package + DRAM. | `_sentinel` |
| `rapl_prefer_psys` | `Optional[bool]` | Prefer psys over package domains for RAPL on Linux (default: False). When True, uses total platform power. | `_sentinel` |
| `metadata` | `Optional[Union[dict, str]]` | Free-form metadata bag to enrich outputs. Either a dict or a path to a JSON file containing a dict. See `EmissionsTracker`. | `_sentinel` |
| `use_national_grid_eso_api` | `Optional[bool]` | Opt-in: when True and the detected location is Great Britain, fetch live carbon intensity from the UK National Grid ESO Carbon Intensity API instead of CodeCarbon's static country-average data. Defaults to False. | `_sentinel` |

Returns:

| Type | Description |
| --- | --- |
|  | The decorated function |

## Task-level tracking

Use these to measure individual tasks inside a single run. See `examples/task_inference.py` and `examples/task_loop_same_task.py`.

## `codecarbon.emissions_tracker.TaskEmissionsTracker`

Track emissions for a specific task This is the context manager for tracking emissions for a specific task. For example:

```
with TaskEmissionsTracker(task_name="Grid search", tracker=tracker):
    grid = GridSearchCV(estimator=model, param_grid=param_grid)
```

## `codecarbon.emissions_tracker.track_task_emissions(fn=None, tracker=None, task_name='')`

Decorator to track emissions specific to a task. With a tracker as input, it will add task emissions to global emissions.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tracker` | `BaseEmissionsTracker` | global tracker used in the current execution. If none is provided, instanciates an emission tracker which will read default parameter from config to enable tracking | `None` |
| `task_name` | `str` | Task to be tracked. If none is provided, an id will be used. | `''` |

Returns:

| Type | Description |
| --- | --- |
|  | The decorated function |
