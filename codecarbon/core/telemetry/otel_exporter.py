"""
OpenTelemetry exporter for CodeCarbon telemetry.

Sends telemetry data to an OTEL-compatible endpoint.
"""

from typing import Any, Dict, Optional

from codecarbon.core.telemetry.collector import TelemetryData
from codecarbon.core.telemetry.config import TelemetryConfig, TelemetryTier
from codecarbon.external.logger import logger

# Try to import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPSpanExporterHTTP

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.debug("OpenTelemetry not available, telemetry will not be exported")


class TelemetryExporter:
    """
    Exports telemetry data via OpenTelemetry.
    
    Supports both gRPC and HTTP exporters.
    """

    def __init__(self, config: TelemetryConfig):
        """
        Initialize the exporter.
        
        Args:
            config: Telemetry configuration
        """
        self._config = config
        self._tracer = None
        self._initialized = False

        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry not installed. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk "
                "opentelemetry-exporter-otlp"
            )
            return

        if not config.is_enabled:
            logger.debug("Telemetry disabled, not initializing exporter")
            return

        self._initialize()

    def _initialize(self) -> None:
        """Initialize OpenTelemetry tracer."""
        if self._initialized:
            return

        try:
            # Set up tracer provider
            provider = TracerProvider()
            trace.set_tracer_provider(provider)

            # Determine endpoint
            endpoint = self._config.otel_endpoint
            if not endpoint:
                logger.debug("No OTEL endpoint configured, skipping exporter init")
                return

            # Choose HTTP or gRPC based on endpoint
            if endpoint.startswith("http://") or endpoint.startswith("https://"):
                # HTTP exporter
                exporter = OTLPSpanExporterHTTP(endpoint=endpoint)
            else:
                # Default to gRPC
                exporter = OTLPSpanExporter(endpoint=endpoint)

            # Add batch processor
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)

            # Get tracer
            self._tracer = trace.get_tracer(__name__)
            self._initialized = True
            logger.info(f"Telemetry exporter initialized with endpoint: {endpoint}")

        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry exporter: {e}")
            self._initialized = False

    def export_telemetry(
        self,
        data: TelemetryData,
        emissions_data: Optional[TelemetryData] = None,
    ) -> bool:
        """
        Export telemetry data.
        
        Args:
            data: The telemetry data to export
            emissions_data: Optional emissions data (only for public tier)
            
        Returns:
            True if export succeeded, False otherwise
        """
        if not self._initialized or not self._tracer:
            logger.debug("Telemetry exporter not initialized, skipping export")
            return False

        if not self._config.is_enabled:
            return False

        try:
            with self._tracer.start_as_current_span("codecarbon.telemetry") as span:
                # Add attributes based on tier
                self._add_attributes(span, data)

                # For public tier, also add emissions data
                if self._config.is_public and emissions_data:
                    self._add_emissions_attributes(span, emissions_data)

            logger.debug("Telemetry data exported successfully")
            return True

        except Exception as e:
            logger.warning(f"Failed to export telemetry: {e}")
            return False

    def _add_attributes(self, span, data: TelemetryData) -> None:
        """Add telemetry attributes to span."""
        # Environment & Hardware (always for internal/public)
        if self._config.is_internal or self._config.is_public:
            span.set_attribute("codecarbon.os", data.os)
            span.set_attribute("codecarbon.python_version", data.python_version)
            span.set_attribute("codecarbon.python_implementation", data.python_implementation)
            span.set_attribute("codecarbon.python_env_type", data.python_env_type)
            span.set_attribute("codecarbon.codecarbon_version", data.codecarbon_version)
            span.set_attribute("codecarbon.codecarbon_install_method", data.codecarbon_install_method)

            # Hardware
            span.set_attribute("codecarbon.cpu_count", data.cpu_count)
            span.set_attribute("codecarbon.cpu_physical_count", data.cpu_physical_count)
            span.set_attribute("codecarbon.cpu_model", data.cpu_model)
            span.set_attribute("codecarbon.cpu_architecture", data.cpu_architecture)
            span.set_attribute("codecarbon.gpu_count", data.gpu_count)
            span.set_attribute("codecarbon.gpu_model", data.gpu_model)
            span.set_attribute("codecarbon.ram_total_gb", data.ram_total_size_gb)

            # CUDA/GPU
            if data.cuda_version:
                span.set_attribute("codecarbon.cuda_version", data.cuda_version)
            if data.gpu_driver_version:
                span.set_attribute("codecarbon.gpu_driver_version", data.gpu_driver_version)

            # Usage patterns
            span.set_attribute("codecarbon.tracking_mode", data.tracking_mode)
            span.set_attribute("codecarbon.api_mode", data.api_mode)
            span.set_attribute("codecarbon.hardware_tracked", ",".join(data.hardware_tracked))
            span.set_attribute("codecarbon.output_methods", ",".join(data.output_methods))
            span.set_attribute("codecarbon.measure_power_interval", data.measure_power_interval_secs)

            # ML Ecosystem
            span.set_attribute("codecarbon.has_torch", data.has_torch)
            span.set_attribute("codecarbon.torch_version", data.torch_version or "")
            span.set_attribute("codecarbon.has_transformers", data.has_transformers)
            span.set_attribute("codecarbon.has_diffusers", data.has_diffusers)
            span.set_attribute("codecarbon.has_tensorflow", data.has_tensorflow)
            span.set_attribute("codecarbon.has_keras", data.has_keras)
            span.set_attribute("codecarbon.ml_framework_primary", data.ml_framework_primary)

            # Context
            span.set_attribute("codecarbon.notebook_environment", data.notebook_environment)
            span.set_attribute("codecarbon.ci_environment", data.ci_environment)
            span.set_attribute("codecarbon.container_runtime", data.container_runtime)
            span.set_attribute("codecarbon.in_container", data.in_container)
            span.set_attribute("codecarbon.python_package_manager", data.python_package_manager)

            # Performance
            span.set_attribute("codecarbon.hardware_detection_success", data.hardware_detection_success)
            span.set_attribute("codecarbon.rapl_available", data.rapl_available)
            span.set_attribute("codecarbon.gpu_detection_method", data.gpu_detection_method)

            # Cloud
            span.set_attribute("codecarbon.cloud_provider", data.cloud_provider)
            span.set_attribute("codecarbon.cloud_region", data.cloud_region)

    def _add_emissions_attributes(self, span, data: TelemetryData) -> None:
        """Add emissions attributes to span (public tier only)."""
        # Emissions data - shared publicly
        span.set_attribute("codecarbon.emissions_kg", data.total_emissions_kg)
        span.set_attribute("codecarbon.emissions_rate_kg_per_sec", data.emissions_rate_kg_per_sec)
        span.set_attribute("codecarbon.energy_consumed_kwh", data.energy_consumed_kwh)
        span.set_attribute("codecarbon.cpu_energy_kwh", data.cpu_energy_kwh)
        span.set_attribute("codecarbon.gpu_energy_kwh", data.gpu_energy_kwh)
        span.set_attribute("codecarbon.ram_energy_kwh", data.ram_energy_kwh)
        span.set_attribute("codecarbon.duration_seconds", data.duration_seconds)
        span.set_attribute("codecarbon.cpu_utilization_avg", data.cpu_utilization_avg)
        span.set_attribute("codecarbon.gpu_utilization_avg", data.gpu_utilization_avg)
        span.set_attribute("codecarbon.ram_utilization_avg", data.ram_utilization_avg)


def create_exporter(config: TelemetryConfig) -> Optional[TelemetryExporter]:
    """
    Create a telemetry exporter based on config.
    
    Args:
        config: Telemetry configuration
        
    Returns:
        TelemetryExporter instance or None if not available
    """
    if not OTEL_AVAILABLE:
        return None
    
    if not config.is_enabled:
        return None
    
    return TelemetryExporter(config)
