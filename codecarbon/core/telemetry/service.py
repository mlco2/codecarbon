"""
Telemetry service - integrates telemetry with CodeCarbon.

This module provides functions to initialize and use telemetry.
"""

from typing import Optional

from codecarbon.core.telemetry.collector import TelemetryCollector, TelemetryData
from codecarbon.core.telemetry.config import (
    TelemetryConfig,
    TelemetryTier,
    get_telemetry_config,
    set_telemetry_tier,
)
from codecarbon.core.telemetry.otel_exporter import TelemetryExporter, create_exporter
from codecarbon.core.telemetry.prompt import prompt_for_telemetry_consent
from codecarbon.external.logger import logger


class TelemetryService:
    """Service for managing telemetry."""

    _instance: Optional["TelemetryService"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._config: Optional[TelemetryConfig] = None
        self._exporter: Optional[TelemetryExporter] = None
        self._collector: Optional[TelemetryCollector] = None
        self._initialized = True

    def initialize(self, force_prompt: bool = False) -> TelemetryConfig:
        """
        Initialize telemetry service.
        
        Args:
            force_prompt: Force showing the consent prompt
            
        Returns:
            TelemetryConfig
        """
        # Get configuration
        self._config = get_telemetry_config()

        # If first run and not forced, try to prompt
        if self._config.first_run and not self._config.has_consent:
            if force_prompt:
                # This will show prompt if needed
                pass

        # Create exporter if enabled
        if self._config.is_enabled:
            self._exporter = create_exporter(self._config)
            self._collector = TelemetryCollector()

        logger.info(
            f"Telemetry initialized: tier={self._config.tier.value}, "
            f"enabled={self._config.is_enabled}"
        )

        return self._config

    def get_config(self) -> Optional[TelemetryConfig]:
        """Get current telemetry config."""
        return self._config

    def collect_and_export(
        self,
        cpu_count: int = 0,
        cpu_physical_count: int = 0,
        cpu_model: str = "",
        gpu_count: int = 0,
        gpu_model: str = "",
        ram_total_gb: float = 0.0,
        tracking_mode: str = "machine",
        api_mode: str = "online",
        output_methods: list = None,
        hardware_tracked: list = None,
        measure_power_interval: float = 15.0,
        rapl_available: bool = False,
        hardware_detection_success: bool = True,
        errors: list = None,
        cloud_provider: str = "",
        cloud_region: str = "",
    ) -> bool:
        """
        Collect and export telemetry data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._config or not self._config.is_enabled:
            return False

        if not self._collector or not self._exporter:
            return False

        try:
            # Collect data
            data = self._collector.collect_all(
                cpu_count=cpu_count,
                cpu_physical_count=cpu_physical_count,
                cpu_model=cpu_model,
                gpu_count=gpu_count,
                gpu_model=gpu_model,
                ram_total_gb=ram_total_gb,
                tracking_mode=tracking_mode,
                api_mode=api_mode,
                output_methods=output_methods,
                hardware_tracked=hardware_tracked,
                measure_power_interval=measure_power_interval,
                rapl_available=rapl_available,
                hardware_detection_success=hardware_detection_success,
                errors=errors,
                cloud_provider=cloud_provider,
                cloud_region=cloud_region,
            )

            # Export
            return self._exporter.export_telemetry(data)

        except Exception as e:
            logger.warning(f"Failed to collect/export telemetry: {e}")
            return False

    def export_emissions(
        self,
        total_emissions_kg: float = 0.0,
        emissions_rate_kg_per_sec: float = 0.0,
        energy_consumed_kwh: float = 0.0,
        cpu_energy_kwh: float = 0.0,
        gpu_energy_kwh: float = 0.0,
        ram_energy_kwh: float = 0.0,
        duration_seconds: float = 0.0,
        cpu_utilization_avg: float = 0.0,
        gpu_utilization_avg: float = 0.0,
        ram_utilization_avg: float = 0.0,
    ) -> bool:
        """
        Export emissions data (only for public tier).
        
        Returns:
            True if successful, False otherwise
        """
        if not self._config or not self._config.is_public:
            return False

        if not self._collector or not self._exporter:
            return False

        try:
            # Collect emissions data
            data = TelemetryData()
            data.collect_emissions(
                total_emissions_kg=total_emissions_kg,
                emissions_rate_kg_per_sec=emissions_rate_kg_per_sec,
                energy_consumed_kwh=energy_consumed_kwh,
                cpu_energy_kwh=cpu_energy_kwh,
                gpu_energy_kwh=gpu_energy_kwh,
                ram_energy_kwh=ram_energy_kwh,
                duration_seconds=duration_seconds,
                cpu_utilization_avg=cpu_utilization_avg,
                gpu_utilization_avg=gpu_utilization_avg,
                ram_utilization_avg=ram_utilization_avg,
            )

            # Export
            return self._exporter.export_telemetry(data)

        except Exception as e:
            logger.warning(f"Failed to export emissions telemetry: {e}")
            return False


# Global instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get the global telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service


def init_telemetry(force_prompt: bool = False) -> TelemetryConfig:
    """
    Initialize telemetry.
    
    Args:
        force_prompt: Force showing consent prompt
        
    Returns:
        TelemetryConfig
    """
    service = get_telemetry_service()
    return service.initialize(force_prompt=force_prompt)


def set_telemetry(tier: str, dont_ask_again: bool = True) -> None:
    """
    Set telemetry tier programmatically.
    
    Args:
        tier: "off", "internal", or "public"
        dont_ask_again: Don't ask again in future
    """
    try:
        tier_enum = TelemetryTier(tier)
        set_telemetry_tier(tier_enum, dont_ask_again=dont_ask_again)
    except ValueError:
        logger.warning(f"Invalid telemetry tier: {tier}")
