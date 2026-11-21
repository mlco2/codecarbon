"""
Base class for live grid carbon intensity providers.

A provider fetches the current carbon intensity of the electricity grid, in
gCO2e/kWh, from an external API. The base class owns what every provider needs
and must get right identically:

* a time-based cache, because grid intensity is published hourly at best while
  emissions are computed on every measurement tick;
* a failure cooldown with exponential backoff, so a bad token or an offline
  machine does not issue one doomed request per tick;
* thread safety, because the measurement thread and ``stop()`` both compute
  emissions; concurrent callers for the same key share a single request.

Cache and cooldown state is per provider class and process-wide, so several
trackers in one process share it. Subclasses key it with ``_cache_key`` (for
instance by location and token) and only implement ``_fetch``.

To add a provider, subclass ``CarbonIntensityProvider`` in a module of this
package and add the class to ``PROVIDER_CLASSES`` in ``__init__.py``.
"""

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Hashable, Mapping, Optional, Type

from codecarbon.core.units import EmissionsPerKWh, Energy
from codecarbon.external.geography import GeoMetadata


class CarbonIntensityError(Exception):
    """A provider could not return a carbon intensity."""


class CarbonIntensityCooldownError(CarbonIntensityError):
    """The request was skipped because a recent one failed."""


@dataclass
class _KeyState:
    value: Optional[float] = None
    fetched_at: float = 0.0
    cooldown_until: float = 0.0
    cooldown_length: float = 0.0


class CarbonIntensityProvider(ABC):
    #: Human-readable name, used in logs.
    name: ClassVar[str]
    #: Seconds a fetched value is served from the cache.
    cache_ttl: ClassVar[float]
    #: First wait after a failure; doubles per consecutive failure up to the max.
    cooldown: ClassVar[float] = 30
    max_cooldown: ClassVar[float] = 3600
    #: Raised for fetch failures and for skipped requests respectively.
    error_class: ClassVar[Type[CarbonIntensityError]] = CarbonIntensityError
    cooldown_error_class: ClassVar[Type[CarbonIntensityCooldownError]] = (
        CarbonIntensityCooldownError
    )

    # Process-wide state, one set per subclass (see __init_subclass__).
    _states: ClassVar[Dict[Hashable, _KeyState]]
    _key_locks: ClassVar[Dict[Hashable, threading.Lock]]
    _registry_lock: ClassVar[threading.Lock]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._states = {}
        cls._key_locks = {}
        cls._registry_lock = threading.Lock()

    @classmethod
    @abstractmethod
    def from_config(
        cls, conf: Mapping[str, Any]
    ) -> Optional["CarbonIntensityProvider"]:
        """Return a provider configured from ``conf``, or None if not enabled."""

    def is_supported(self, geo: GeoMetadata) -> bool:
        """Whether this provider covers ``geo``. Defaults to everywhere."""
        return True

    @abstractmethod
    def _cache_key(self, geo: GeoMetadata) -> Hashable:
        """Key the cache and cooldown: requests with the same key share them."""

    @abstractmethod
    def _fetch(self, geo: GeoMetadata) -> float:
        """Call the API and return the carbon intensity in gCO2e/kWh."""

    @classmethod
    def reset_cache(cls) -> None:
        """Drop the cached intensities and any pending failure cooldown."""
        with cls._registry_lock:
            cls._states.clear()

    @classmethod
    def _lock_and_state(cls, key: Hashable) -> "tuple[threading.Lock, _KeyState]":
        with cls._registry_lock:
            lock = cls._key_locks.setdefault(key, threading.Lock())
            state = cls._states.setdefault(key, _KeyState())
        return lock, state

    def get_carbon_intensity(self, geo: GeoMetadata) -> float:
        """
        Return the grid carbon intensity for ``geo`` in gCO2e/kWh, cached.

        Raises:
            error_class: the request failed or returned unusable data.
            cooldown_error_class: the request was skipped because a recent one
                failed.
        """
        key = self._cache_key(geo)
        lock, state = self._lock_and_state(key)
        # Held across the request so that concurrent callers with an expired
        # cache make a single request instead of one each.
        with lock:
            now = time.monotonic()
            if state.value is not None and now - state.fetched_at < self.cache_ttl:
                return state.value

            remaining = state.cooldown_until - now
            if remaining > 0:
                raise self.cooldown_error_class(
                    f"{self.name} API is in cooldown after a previous failure, "
                    f"retrying in {remaining:.0f} seconds"
                )

            try:
                value = self._fetch(geo)
            except Exception:
                state.cooldown_length = min(
                    max(state.cooldown_length * 2, self.cooldown), self.max_cooldown
                )
                state.cooldown_until = time.monotonic() + state.cooldown_length
                raise

            state.value = value
            state.fetched_at = time.monotonic()
            state.cooldown_until = state.cooldown_length = 0.0
            return value

    def get_emissions(self, energy: Energy, geo: GeoMetadata) -> float:
        """Return the emissions of ``energy`` consumed at ``geo``, in kg CO2e."""
        intensity = EmissionsPerKWh.from_g_per_kWh(self.get_carbon_intensity(geo))
        return intensity.kgs_per_kWh * energy.kWh
