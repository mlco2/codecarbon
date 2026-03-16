"""
OpenLlmety output method for CodeCarbon.

This module provides integration with OpenLlmety (OpenTelemetry-based LLM observability)
to send CodeCarbon emissions data as attributes on OpenTelemetry spans.

This allows emissions data to appear alongside LLM traces in LangFuse, LangSmith,
or any other OpenTelemetry-compatible backend.

Usage:
    # Via environment variable:
    # export CODECARBON_OPENLLMETRY=true
    
    # Or programmatically:
    from codecarbon import enable_openllmetry
    enable_openllmetry()
    
    # Then use CodeCarbon normally
    from codecarbon import EmissionsTracker
    with EmissionsTracker() as tracker:
        # Your code here
        pass
"""

from typing import Optional

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData


class OpenLlmetyOutput(BaseOutput):
    """
    Send emissions data to OpenLlmety/OpenTelemetry spans.
    
    This output method injects CodeCarbon emissions data as custom attributes
    on the currently active OpenTelemetry span. This allows emissions data
    to appear alongside LLM traces in LangFuse, LangSmith, or other
    OpenTelemetry-compatible backends.
    
    The integration works automatically when OpenLlmety instrumentation is
    initialized in the user's application.
    """

    def __init__(self, service_name: Optional[str] = None):
        """
        Initialize the OpenLlmety output.
        
        Args:
            service_name: Optional service name for the tracer.
        """
        self._tracer = None
        self._span = None
        self._service_name = service_name or "codecarbon"
        
        try:
            from opentelemetry import trace
            from opentelemetry.trace import Status, StatusCode
            
            self._trace = trace
            self._StatusCode = StatusCode
            self._Status = Status
            self._initialized = True
            logger.debug("OpenLlmety/OpenTelemetry integration initialized")
        except ImportError:
            logger.warning(
                "OpenTelemetry is not installed. "
                "Please install it with: pip install opentelemetry-api opentelemetry-sdk\n"
                "Or install codecarbon with openllmetry extras: pip install codecarbon[openllmetry]"
            )
            self._initialized = False

    def _get_current_span(self):
        """
        Get the currently active span from the OpenTelemetry context.
        
        Returns:
            The current span or None if no span is active.
        """
        if not self._initialized:
            return None
            
        try:
            from opentelemetry import trace
            
            # Get the currently active tracer
            tracer = trace.get_tracer(self._service_name)
            
            # Get the current span from the context
            span = trace.get_current_span()
            return span
        except Exception as e:
            logger.debug(f"Could not get current OpenTelemetry span: {e}")
            return None

    def _set_span_attributes(self, emissions_data: EmissionsData):
        """
        Set CodeCarbon attributes on the current span.
        
        Args:
            emissions_data: The emissions data to set as attributes.
        """
        if not self._initialized:
            return
            
        span = self._get_current_span()
        if span is None:
            # No active span - this is fine, emissions will not be traced
            # but we don't want to create unnecessary noise
            return
            
        try:
            # Set emissions data as span attributes
            span.set_attribute("codecarbon.emissions_kg", emissions_data.emissions)
            span.set_attribute("codecarbon.energy_consumed_kwh", emissions_data.energy_consumed)
            span.set_attribute("codecarbon.duration_seconds", emissions_data.duration)
            span.set_attribute("codecarbon.emissions_rate_kg_per_sec", emissions_data.emissions_rate)
            span.set_attribute("codecarbon.cpu_power_watts", emissions_data.cpu_power)
            span.set_attribute("codecarbon.gpu_power_watts", emissions_data.gpu_power)
            span.set_attribute("codecarbon.ram_power_watts", emissions_data.ram_power)
            span.set_attribute("codecarbon.cpu_energy_kwh", emissions_data.cpu_energy)
            span.set_attribute("codecarbon.gpu_energy_kwh", emissions_data.gpu_energy)
            span.set_attribute("codecarbon.ram_energy_kwh", emissions_data.ram_energy)
            span.set_attribute("codecarbon.country", emissions_data.country_name or "")
            span.set_attribute("codecarbon.region", emissions_data.region or "")
            span.set_attribute("codecarbon.cloud_provider", emissions_data.cloud_provider or "")
            span.set_attribute("codecarbon.cloud_region", emissions_data.cloud_region or "")
            
            # Set status if emissions were recorded
            if emissions_data.emissions > 0:
                span.set_status(self._Status(self._StatusCode.OK))
                
        except Exception as e:
            logger.debug(f"Could not set OpenTelemetry span attributes: {e}")

    def out(self, total: EmissionsData, delta: EmissionsData):
        """
        Send emissions data to the current OpenTelemetry span.
        
        This is called when the tracker stops or flushes.
        
        Args:
            total: Total emissions data since tracking started.
            delta: Delta emissions since last measurement.
        """
        if not self._initialized:
            return
            
        try:
            # Set total emissions on the span
            self._set_span_attributes(total)
            logger.debug("CodeCarbon emissions data sent to OpenLlmety")
        except Exception as e:
            logger.error(f"Error sending to OpenLlmety: {e}")

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        """
        Send live emissions data to the current OpenTelemetry span.
        
        This is called at regular intervals during tracking.
        
        Args:
            total: Total emissions data since tracking started.
            delta: Delta emissions since last measurement.
        """
        if not self._initialized:
            return
            
        try:
            # For live updates, we set the delta (recent activity)
            self._set_span_attributes(delta)
        except Exception as e:
            logger.debug(f"Error in live_out to OpenLlmety: {e}")


# Global state for enabling OpenLlmety integration
_openllmetry_enabled = False


def enable_openllmetry(service_name: Optional[str] = None) -> bool:
    """
    Enable OpenLlmety integration for CodeCarbon.
    
    This function enables the OpenLlmety output method, which will send
    CodeCarbon emissions data as attributes on OpenTelemetry spans.
    
    This works automatically with any OpenLlmety-integrated LLM framework
    (LangChain, OpenAI, etc.) and any compatible backend (LangFuse, LangSmith, etc.).
    
    Args:
        service_name: Optional service name for the tracer.
        
    Returns:
        True if successfully enabled, False otherwise.
        
    Example:
        >>> from codecarbon import enable_openllmetry
        >>> enable_openllmetry()
        True
        
        >>> # Or with a custom service name
        >>> enable_openllmetry(service_name="my-llm-service")
        True
    """
    global _openllmetry_enabled
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        
        # Set up a basic tracer provider if not already set
        try:
            trace.get_tracer_provider()
        except Exception:
            # No provider set, create a default one
            trace.set_tracer_provider(TracerProvider())
        
        _openllmetry_enabled = True
        logger.info("OpenLlmety integration enabled for CodeCarbon")
        return True
    except ImportError:
        logger.error(
            "OpenTelemetry is not installed. "
            "Please install it with: pip install opentelemetry-api opentelemetry-sdk\n"
            "Or install codecarbon with openllmetry extras: pip install codecarbon[openllmetry]"
        )
        return False


def disable_openllmetry() -> None:
    """
    Disable OpenLlmety integration for CodeCarbon.
    """
    global _openllmetry_enabled
    _openllmetry_enabled = False
    logger.info("OpenLlmety integration disabled for CodeCarbon")


def is_openllmetry_enabled() -> bool:
    """
    Check if OpenLlmety integration is enabled.
    
    Returns:
        True if enabled, False otherwise.
    """
    return _openllmetry_enabled
