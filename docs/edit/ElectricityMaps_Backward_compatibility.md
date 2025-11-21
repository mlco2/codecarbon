# Backward Compatibility for CO2 Signal → Electricity Maps Migration

## Summary

The API formerly known as CO2 Signal has been rebranded to Electricity Maps, and their API has been updated from v1 to v3. To maintain backward compatibility while adopting the new naming, we've implemented the following changes:

## Parameter Renaming

| Old Parameter Name | New Parameter Name | Status |
|-------------------|-------------------|---------|
| `co2_signal_api_token` | `electricitymaps_api_token` | Old name deprecated but still supported |
| `CO2SignalAPIError` | `ElectricityMapsAPIError` | Old name removed |
| `co2_signal` module | `electricitymaps_api` module | Old name removed |

## Backward Compatibility Features

### 1. Parameter Aliases

The old parameter name `co2_signal_api_token` is still accepted in all APIs:

```python
# Both work, but the old name emits a deprecation warning
tracker = EmissionsTracker(co2_signal_api_token="your-token")  # Deprecated
tracker = EmissionsTracker(electricitymaps_api_token="your-token")  # Recommended
```

### 2. Configuration File Support

Configuration files can use either the old or new parameter name:

```ini
[codecarbon]
# Old name (deprecated, but still works)
co2_signal_api_token=your-token

# New name (recommended)
electricitymaps_api_token=your-token
```

### 3. Deprecation Warnings

When using the old parameter name, a warning is logged:

```
WARNING: Parameter 'co2_signal_api_token' is deprecated and will be removed in a future version. 
Please use 'electricitymaps_api_token' instead.
```

## Migration Guide

### For Users

**No immediate action required.** Your existing code will continue to work, but you'll see deprecation warnings.

To migrate:

1. Replace `co2_signal_api_token` with `electricitymaps_api_token` in your code
2. Update your `.codecarbon.config` files to use the new parameter name
3. Update your environment variables from `CODECARBON_CO2_SIGNAL_API_TOKEN` to `CODECARBON_ELECTRICITYMAPS_API_TOKEN`

Example migration:

```python
# Before
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    co2_signal_api_token="your-token"
)

# After
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    electricitymaps_api_token="your-token"
)
```

### For Developers

When both old and new parameters are provided:
- The new parameter takes precedence
- A deprecation warning is still emitted for the old parameter

Implementation details:
- `BaseEmissionsTracker.__init__()` handles the parameter migration
- `Emissions.__init__()` handles the parameter migration for the core class
- `track_emissions()` decorator handles the parameter migration
- Configuration file reading checks both parameter names

## Timeline

- **v3.1.0**: New parameter introduced, old parameter deprecated
- **v4.0.0** (planned): Old parameter will be removed

## Testing

Backward compatibility is tested in:
- `tests/test_backward_compatibility.py` - Tests parameter aliases
- `tests/test_config_backward_compatibility.py` - Tests configuration file support

Run tests with:
```bash
uv run pytest tests/test_backward_compatibility.py tests/test_config_backward_compatibility.py -v
```
