"""Tests for the EmissionsEquivalences engine."""

import pytest

from codecarbon.core.equivalences import EmissionsEquivalences, EquivalenceResult


class TestEmissionsEquivalences:
    """Tests for the EmissionsEquivalences.compute() method."""

    def setup_method(self):
        self.eq = EmissionsEquivalences()

    def test_compute_returns_equivalence_result(self):
        result = self.eq.compute(1.0)
        assert isinstance(result, EquivalenceResult)

    def test_compute_zero_emissions(self):
        result = self.eq.compute(0.0)
        assert result.emissions_kg == 0.0
        assert result.car_km == 0.0
        assert result.flights_paris_nyc == 0.0
        assert result.tv_hours == 0.0
        assert result.smartphone_charges == 0.0
        assert result.tree_months == 0.0
        assert result.household_percentage == 0.0
        assert result.led_bulb_hours == 0.0
        assert result.streaming_hours == 0.0

    def test_compute_negative_emissions_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            self.eq.compute(-1.0)

    def test_compute_one_kg_car_km(self):
        result = self.eq.compute(1.0)
        expected_km = 1.0 / EmissionsEquivalences.KG_CO2_PER_KM
        assert result.car_km == pytest.approx(expected_km)

    def test_compute_one_kg_flights(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_FLIGHT_CDG_JFK
        assert result.flights_paris_nyc == pytest.approx(expected)

    def test_compute_one_kg_tv_hours(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_TV_HOUR
        assert result.tv_hours == pytest.approx(expected)

    def test_compute_one_kg_smartphone_charges(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_SMARTPHONE_CHARGE
        assert result.smartphone_charges == pytest.approx(expected)

    def test_compute_one_kg_tree_months(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_TREE_MONTH
        assert result.tree_months == pytest.approx(expected)

    def test_compute_one_kg_household_percentage(self):
        result = self.eq.compute(1.0)
        expected = (1.0 / EmissionsEquivalences.KG_CO2_PER_US_HOUSEHOLD_WEEK) * 100
        assert result.household_percentage == pytest.approx(expected)

    def test_compute_one_kg_led_hours(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_LED_HOUR
        assert result.led_bulb_hours == pytest.approx(expected)

    def test_compute_one_kg_streaming(self):
        result = self.eq.compute(1.0)
        expected = 1.0 / EmissionsEquivalences.KG_CO2_PER_STREAMING_HOUR
        assert result.streaming_hours == pytest.approx(expected)

    def test_compute_large_emissions(self):
        """Test with 1000 kg (1 tonne) — should scale linearly."""
        result_1 = self.eq.compute(1.0)
        result_1000 = self.eq.compute(1000.0)
        assert result_1000.car_km == pytest.approx(result_1.car_km * 1000)
        assert result_1000.tv_hours == pytest.approx(result_1.tv_hours * 1000)

    def test_compute_small_emissions(self):
        """Test with 0.001 kg (1 gram) — should still produce valid results."""
        result = self.eq.compute(0.001)
        assert result.emissions_kg == 0.001
        assert result.car_km > 0
        assert result.smartphone_charges > 0

    def test_round_digits(self):
        result = self.eq.compute(1.0, round_digits=2)
        # All values should be rounded to 2 decimal places
        assert result.car_km == round(1.0 / EmissionsEquivalences.KG_CO2_PER_KM, 2)

    def test_round_digits_zero(self):
        result = self.eq.compute(1.5, round_digits=0)
        assert isinstance(result.car_km, float)
        assert result.car_km == round(1.5 / EmissionsEquivalences.KG_CO2_PER_KM, 0)

    def test_emissions_kg_preserved(self):
        result = self.eq.compute(42.5)
        assert result.emissions_kg == 42.5


class TestEquivalenceResult:
    """Tests for the EquivalenceResult dataclass."""

    def _make_result(self, emissions_kg=1.0):
        eq = EmissionsEquivalences()
        return eq.compute(emissions_kg)

    def test_to_dict_returns_dict(self):
        result = self._make_result()
        d = result.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_all_keys(self):
        result = self._make_result()
        d = result.to_dict()
        expected_keys = {
            "emissions_kg",
            "car_km",
            "flights_paris_nyc",
            "tv_hours",
            "smartphone_charges",
            "tree_months",
            "household_percentage",
            "led_bulb_hours",
            "streaming_hours",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_values_match_attributes(self):
        result = self._make_result()
        d = result.to_dict()
        assert d["emissions_kg"] == result.emissions_kg
        assert d["car_km"] == result.car_km
        assert d["flights_paris_nyc"] == result.flights_paris_nyc

    def test_format_human_readable_returns_string(self):
        result = self._make_result()
        text = result.format_human_readable()
        assert isinstance(text, str)

    def test_format_human_readable_contains_key_info(self):
        result = self._make_result()
        text = result.format_human_readable()
        assert "CO₂eq" in text
        assert "Car travel" in text
        assert "Flights" in text
        assert "TV watching" in text
        assert "Smartphone" in text
        assert "Tree" in text
        assert "household" in text
        assert "LED" in text
        assert "streaming" in text

    def test_format_human_readable_zero_emissions(self):
        result = self._make_result(0.0)
        text = result.format_human_readable()
        assert "0.000 kg CO₂eq" in text

    def test_format_distance_large(self):
        assert EquivalenceResult._format_distance(1500.0) == "1,500 km"

    def test_format_distance_small(self):
        assert EquivalenceResult._format_distance(5.3) == "5.3 km"

    def test_format_flights_large(self):
        assert "one-way flights" in EquivalenceResult._format_flights(2.5)

    def test_format_flights_small(self):
        result = EquivalenceResult._format_flights(0.003)
        assert "0.003" in result

    def test_format_time_minutes(self):
        assert "minutes" in EquivalenceResult._format_time(0.5)

    def test_format_time_hours(self):
        assert "hours" in EquivalenceResult._format_time(5.0)

    def test_format_time_days(self):
        assert "days" in EquivalenceResult._format_time(48.0)

    def test_format_time_years(self):
        assert "years" in EquivalenceResult._format_time(24 * 400)

    def test_format_count_small(self):
        assert "50 charges" in EquivalenceResult._format_count(50)

    def test_format_count_thousands(self):
        result = EquivalenceResult._format_count(5000)
        assert "5,000" in result

    def test_format_count_millions(self):
        result = EquivalenceResult._format_count(2_500_000)
        assert "M charges" in result

    def test_format_tree_time_months(self):
        assert "tree-months" in EquivalenceResult._format_tree_time(6.0)

    def test_format_tree_time_years(self):
        assert "tree-years" in EquivalenceResult._format_tree_time(24.0)
