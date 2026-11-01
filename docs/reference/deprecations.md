# Deprecations and migrations

Everything in CodeCarbon that still works but is on its way out: when it was
deprecated, when it is scheduled to be removed, and what to use instead.

User-visible changes per release are on the
[GitHub releases page](https://github.com/mlco2/codecarbon/releases).

| Deprecated | Since | Removal | Replacement |
|---|---|---|---|
| `codecarbon[viz-legacy]` extra | 3.2.1 | 4.0.0 | `codecarbon[carbonboard]` |
| `save_to_file`, `save_to_api`, `save_to_logger`, `save_to_prometheus`, `save_to_logfire` parameters | 3.2.8 | Not scheduled | `output_methods=[...]` |
| `co2_signal_api_token` parameter and config key | 3.1.1 | Not scheduled | `electricitymaps_api_token` |

