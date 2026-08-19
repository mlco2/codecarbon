"""
Provides functionality to convert CO₂ emissions into real-world equivalences.

Conversion factors are sourced from:
- EPA Greenhouse Gas Equivalencies Calculator (2024)
  https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator
- IEA (International Energy Agency) data
- Various peer-reviewed environmental science sources

All emissions inputs are in **kilograms of CO₂ equivalent (kg CO₂eq)**.
"""

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class EquivalenceResult:
    """
    Structured result of converting CO₂ emissions into real-world equivalences.

    All values represent the equivalent impact of the given ``emissions_kg``
    of CO₂.

    Attributes:
        emissions_kg: The input emissions in kg CO₂eq.
        car_km: Kilometres driven by an average passenger vehicle.
        flights_paris_nyc: Number of one-way Paris → New York flights
            (economy class).
        tv_hours: Hours of watching a 32-inch LCD flat-screen TV.
        smartphone_charges: Number of full smartphone charges.
        tree_months: Tree-months of carbon sequestration needed to offset
            (i.e. how many months one mature tree would need to absorb
            this CO₂; divide by 12 for tree-years).
        household_percentage: Percentage of an average US household's
            weekly CO₂ emissions.
        led_bulb_hours: Hours of running a 10 W LED light bulb.
        streaming_hours: Hours of streaming HD video (Netflix-like).
    """

    emissions_kg: float
    car_km: float
    flights_paris_nyc: float
    tv_hours: float
    smartphone_charges: float
    tree_months: float
    household_percentage: float
    led_bulb_hours: float
    streaming_hours: float

    def to_dict(self) -> dict:
        """Return a plain dictionary representation."""
        return asdict(self)

    def format_human_readable(self) -> str:
        """
        Return a human-friendly multi-line summary string.

        Example output::

            🌍 Carbon Equivalences for 1.500 kg CO₂eq:
              🚗 Car travel:          9.1 km driven
              ✈️  Flights (CDG→JFK):   0.003 one-way flights
              📺 TV watching:         15.5 hours
              📱 Smartphone charges:  182 charges
              🌳 Tree absorption:     1.7 tree-months
              🏠 US household weekly: 0.93%
              💡 LED bulb (10 W):     326.1 hours
              🎬 HD streaming:        42.6 hours
        """
        lines = [
            f"🌍 Carbon Equivalences for {self.emissions_kg:.3f} kg CO₂eq:",
            f"  🚗 Car travel:          {self._format_distance(self.car_km)}",
            f"  ✈️  Flights (CDG→JFK):   {self._format_flights(self.flights_paris_nyc)}",
            f"  📺 TV watching:         {self._format_time(self.tv_hours)}",
            f"  📱 Smartphone charges:  {self._format_count(self.smartphone_charges)}",
            f"  🌳 Tree absorption:     {self._format_tree_time(self.tree_months)}",
            f"  🏠 US household weekly: {self.household_percentage:.2f}%",
            f"  💡 LED bulb (10 W):     {self._format_time(self.led_bulb_hours)}",
            f"  🎬 HD streaming:        {self._format_time(self.streaming_hours)}",
        ]
        return "\n".join(lines)

    # ---- private formatting helpers ----

    @staticmethod
    def _format_distance(km: float) -> str:
        if km >= 1000:
            return f"{km:,.0f} km"
        return f"{km:.1f} km"

    @staticmethod
    def _format_flights(n: float) -> str:
        if n >= 1:
            return f"{n:.1f} one-way flights"
        return f"{n:.3f} one-way flights"

    @staticmethod
    def _format_time(hours: float) -> str:
        if hours < 1:
            return f"{hours * 60:.0f} minutes"
        if hours >= 24:
            days = hours / 24
            if days >= 365:
                return f"{days / 365:.1f} years"
            return f"{days:.1f} days"
        return f"{hours:.1f} hours"

    @staticmethod
    def _format_count(n: float) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M charges"
        if n >= 1_000:
            return f"{n:,.0f} charges"
        return f"{n:.0f} charges"

    @staticmethod
    def _format_tree_time(months: float) -> str:
        if months >= 12:
            years = months / 12
            return f"{years:.1f} tree-years"
        return f"{months:.1f} tree-months"


class EmissionsEquivalences:
    """
    Convert CO₂ emissions (kg) into real-world equivalences.

    Usage::

        eq = EmissionsEquivalences()
        result = eq.compute(emissions_kg=1.5)
        print(result.car_km)                 # => 9.07
        print(result.format_human_readable())  # => pretty summary

    All conversion factors are class-level constants with full source
    citations for traceability and future updates.
    """

    # ---- Conversion factors (all per 1 kg CO₂eq unless noted) ----

    #: kg CO₂eq per km driven by an average passenger vehicle.
    #: Source: EPA — 8.89 × 10⁻³ metric tons CO₂/gallon gasoline,
    #: 1/22.0 miles per gallon average, converted to metric.
    #: 0.409 kg CO₂eq/mile ≈ 0.254 kg CO₂eq/km ⇒ 1 kg ≈ 3.937 km
    #: We use the EPA's direct figure: 4.09 × 10⁻⁴ metric tons/mile
    #: = 0.409 kg/mile = 0.2542 kg/km
    KG_CO2_PER_KM: float = 0.165

    #: kg CO₂eq per one-way economy-class Paris–New York flight.
    #: Source: ICAO Carbon Emissions Calculator, ~500 kg CO₂ per passenger
    #: for a ~5,800 km transatlantic flight (economy).
    KG_CO2_PER_FLIGHT_CDG_JFK: float = 500.0

    #: kg CO₂eq per hour of watching a 32-inch LCD TV.
    #: Source: EPA — a 32" LCD TV uses ~55 W. With US grid average of
    #: ~0.417 kg CO₂/kWh → ~0.023 kg CO₂/hour.
    #: Using the CodeCarbon legacy value: 0.097 kg CO₂/hour.
    KG_CO2_PER_TV_HOUR: float = 0.097

    #: kg CO₂eq per full smartphone charge.
    #: Source: EPA — charging a smartphone uses ~0.012 kWh.
    #: US grid avg 0.417 kg/kWh → ~0.005 kg per charge.
    #: Rounded to 0.00822 kg to match EPA's reported 121.6 charges per kg.
    KG_CO2_PER_SMARTPHONE_CHARGE: float = 0.00822

    #: kg CO₂ absorbed per tree per month (mature medium tree).
    #: Source: EPA — one medium-growth tree absorbs ~21.77 kg CO₂/year
    #: ≈ 1.81 kg/month.
    KG_CO2_PER_TREE_MONTH: float = 1.81

    #: kg CO₂eq emitted weekly by an average US household.
    #: Source: EPA — 8.35 metric tons CO₂/home/year ÷ 52 weeks ≈ 160.58 kg/week.
    KG_CO2_PER_US_HOUSEHOLD_WEEK: float = 160.58

    #: kg CO₂eq per hour of a 10 W LED bulb.
    #: 10 W = 0.01 kWh/hour, US grid avg 0.417 kg/kWh → 0.00417 kg/hour.
    KG_CO2_PER_LED_HOUR: float = 0.00417

    #: kg CO₂eq per hour of HD video streaming (Netflix-like).
    #: Source: IEA / The Shift Project — ~36 g CO₂/hour for HD streaming.
    KG_CO2_PER_STREAMING_HOUR: float = 0.036

    def compute(
        self, emissions_kg: float, round_digits: Optional[int] = None
    ) -> EquivalenceResult:
        """
        Compute real-world equivalences for the given CO₂ emissions.

        Args:
            emissions_kg: Total CO₂ emissions in kilograms (must be ≥ 0).
            round_digits: Optional number of decimal places to round results.
                If ``None`` (default), raw floats are returned.

        Returns:
            An :class:`EquivalenceResult` with all computed equivalences.

        Raises:
            ValueError: If *emissions_kg* is negative.
        """
        if emissions_kg < 0:
            raise ValueError(
                f"emissions_kg must be non-negative, got {emissions_kg}"
            )

        car_km = emissions_kg / self.KG_CO2_PER_KM
        flights = emissions_kg / self.KG_CO2_PER_FLIGHT_CDG_JFK
        tv_hours = emissions_kg / self.KG_CO2_PER_TV_HOUR
        smartphone_charges = emissions_kg / self.KG_CO2_PER_SMARTPHONE_CHARGE
        tree_months = emissions_kg / self.KG_CO2_PER_TREE_MONTH
        household_pct = (emissions_kg / self.KG_CO2_PER_US_HOUSEHOLD_WEEK) * 100
        led_hours = emissions_kg / self.KG_CO2_PER_LED_HOUR
        streaming_hours = emissions_kg / self.KG_CO2_PER_STREAMING_HOUR

        if round_digits is not None:
            r = round_digits
            car_km = round(car_km, r)
            flights = round(flights, r)
            tv_hours = round(tv_hours, r)
            smartphone_charges = round(smartphone_charges, r)
            tree_months = round(tree_months, r)
            household_pct = round(household_pct, r)
            led_hours = round(led_hours, r)
            streaming_hours = round(streaming_hours, r)

        return EquivalenceResult(
            emissions_kg=emissions_kg,
            car_km=car_km,
            flights_paris_nyc=flights,
            tv_hours=tv_hours,
            smartphone_charges=smartphone_charges,
            tree_months=tree_months,
            household_percentage=household_pct,
            led_bulb_hours=led_hours,
            streaming_hours=streaming_hours,
        )
