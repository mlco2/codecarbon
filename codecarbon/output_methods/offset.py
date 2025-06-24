"""
Carbon offset integration with OneClickImpact API
"""

import logging

try:
    from makeimpact import Environment, OneClickImpact

    MAKEIMPACT_AVAILABLE = True
except ImportError:
    MAKEIMPACT_AVAILABLE = False

from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData

logger = logging.getLogger(__name__)


class OneClickImpactOutput(BaseOutput):
    """
    Output handler for automatic carbon offsetting via OneClickImpact API
    """

    def __init__(
        self,
        api_key: str,
        environment: str = "sandbox",
        offset_threshold: float = 0.5,
        auto_offset: bool = True,
    ):
        """
        Initialize OneClickImpact output handler

        Args:
            api_key: OneClickImpact API key
            environment: API environment ("sandbox" or "production")
            offset_threshold: Minimum accumulated emissions (kg CO2) before triggering offset
            auto_offset: Whether to automatically offset when threshold is reached
        """
        if not MAKEIMPACT_AVAILABLE:
            raise ImportError(
                "makeimpact package is required for OneClickImpact integration. "
                "Install it with: pip install makeimpact"
            )

        self.api_key = api_key
        self.environment = environment
        # Ensure minimum threshold of 0.5 kg (converts to ~1.1 lbs)
        self.offset_threshold = max(offset_threshold, 0.5)
        self.auto_offset = auto_offset
        self.accumulated_emissions_kg = 0.0

        # Initialize OneClickImpact SDK
        env = (
            Environment.SANDBOX if environment == "sandbox" else Environment.PRODUCTION
        )
        self.sdk = OneClickImpact(api_key=api_key, environment=env)

        logger.info(
            f"OneClickImpact output initialized - Environment: {environment}, "
            f"Threshold: {self.offset_threshold} kg CO2, Auto-offset: {auto_offset}"
        )

    def out(self, data: EmissionsData, experiment_data: EmissionsData) -> None:
        """
        Process emissions data and trigger offset if conditions are met

        Args:
            data: Current emissions data
            experiment_data: Cumulative experiment data
        """
        # Always accumulate emissions regardless of auto_offset setting
        # This allows for manual offsetting later even when auto_offset is disabled
        self.accumulated_emissions_kg += data.emissions

        logger.debug(
            f"Accumulated emissions: {self.accumulated_emissions_kg:.6f} kg CO2 "
            f"(threshold: {self.offset_threshold} kg)"
        )

        # Only trigger automatic offset if auto_offset is enabled
        if self.auto_offset and self.accumulated_emissions_kg >= self.offset_threshold:
            if self._offset_emissions(self.accumulated_emissions_kg):
                logger.info(
                    f"Successfully offset {self.accumulated_emissions_kg:.6f} kg CO2 "
                    f"({self._kg_to_lbs(self.accumulated_emissions_kg)} lbs)"
                )
                self.accumulated_emissions_kg = 0.0  # Reset after successful offset
            else:
                logger.warning("Failed to offset accumulated emissions")

    def manual_offset(self) -> bool:
        """
        Manually trigger offset for accumulated emissions

        Returns:
            bool: True if offset was successful, False otherwise
        """
        if self.accumulated_emissions_kg <= 0:
            logger.warning("No accumulated emissions to offset")
            return False

        emissions_to_offset = self.accumulated_emissions_kg
        if self._offset_emissions(emissions_to_offset):
            logger.info(
                f"Manual offset successful: {emissions_to_offset:.6f} kg CO2 "
                f"({self._kg_to_lbs(emissions_to_offset)} lbs)"
            )
            self.accumulated_emissions_kg = 0.0  # Reset after successful offset
            return True
        else:
            logger.error("Manual offset failed")
            return False

    def _offset_emissions(self, emissions_kg: float) -> bool:
        """
        Offset emissions via OneClickImpact API

        Args:
            emissions_kg: Amount of CO2 emissions in kg to offset

        Returns:
            bool: True if offset was successful, False otherwise
        """
        try:
            # Convert kg to lbs and round to nearest integer
            emissions_lbs = self._kg_to_lbs(emissions_kg)

            # Don't call API for amounts less than 1 lb
            if emissions_lbs < 1:
                logger.debug(
                    f"Emissions amount too small for offset: {emissions_kg:.6f} kg "
                    f"({emissions_lbs} lbs). Minimum is 1 lb."
                )
                return False

            logger.info(f"Attempting to offset {emissions_lbs} lbs of CO2")

            # Call OneClickImpact API to purchase carbon credits
            response = self.sdk.capture_carbon(amount=emissions_lbs)

            if response and response.get("status") == "success":
                logger.info(f"Carbon offset successful: {emissions_lbs} lbs CO2")
                return True
            else:
                logger.error(f"Carbon offset failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Error during carbon offset: {str(e)}")
            return False

    def _kg_to_lbs(self, kg: float) -> int:
        """
        Convert kilograms to pounds and round to nearest integer

        Args:
            kg: Weight in kilograms

        Returns:
            int: Weight in pounds, rounded to nearest integer
        """
        # 1 kg = 2.20462 lbs
        return round(kg * 2.20462)

    def get_accumulated_emissions(self) -> float:
        """
        Get the current accumulated emissions in kg CO2

        :return: Accumulated emissions in kg CO2
        """
        return self.accumulated_emissions_kg
